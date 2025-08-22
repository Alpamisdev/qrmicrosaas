from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import hmac
import hashlib
import os
from datetime import datetime

from app.db import get_async_session
from app.crud_user import get_user_by_email
from app.crud_subscription import (
    create_subscription,
    get_subscription_by_lemon_id,
    get_latest_subscription_for_user,
    update_subscription,
)


router = APIRouter()


def _validate_signature(secret: str, raw_body: bytes, signature: str) -> bool:
    if not signature:
        return False
    mac = hmac.new(secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(mac, signature)
    except Exception:
        return False


@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    secret = os.getenv("LEMON_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    raw = await request.body()
    signature = request.headers.get("X-Signature") or request.headers.get("X-Signature-Hash")
    if not _validate_signature(secret, raw, signature or ""):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    meta = payload.get("meta") or {}
    event = meta.get("event_name")
    data = payload.get("data") or {}
    attributes = data.get("attributes") or {}

    lemon_id = str(data.get("id")) if data.get("id") is not None else None
    status = attributes.get("status")  # on_trial, active, canceled, expired, etc.
    user_email = attributes.get("user_email")
    # Try to get user_id from custom data if provided during checkout
    custom_meta = meta.get("custom_data") or meta.get("custom") or {}
    try:
        user_id_custom = int(custom_meta.get("user_id")) if custom_meta.get("user_id") is not None else None
    except Exception:
        user_id_custom = None
    renews_at_str = attributes.get("renews_at")
    ends_at_str = attributes.get("ends_at") or attributes.get("trial_ends_at")
    variant_id = attributes.get("variant_id")

    def parse_dt(val: str | None) -> datetime | None:
        if not val:
            return None
        try:
            # Example: 2025-08-25T13:50:49.000000Z
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None

    renews_at = parse_dt(renews_at_str)
    ends_at = parse_dt(ends_at_str)

    # Map plan by variant_id if needed
    plan = "monthly" if variant_id == 954787 else "yearly" if variant_id else "paid"

    if event == "subscription_created":
        user = None
        if user_id_custom is not None:
            from app.crud_user import get_user_by_id
            user = await get_user_by_id(session, int(user_id_custom))
        if not user and user_email:
            user = await get_user_by_email(session, user_email)
        if not user:
            return {"ok": True}
        existing = None
        if lemon_id:
            existing = await get_subscription_by_lemon_id(session, lemon_id)
        if existing:
            await update_subscription(
                session,
                existing.id,
                status=status or existing.status,
                plan=plan or existing.plan,
                renews_at=renews_at,
                ends_at=ends_at,
            )
        else:
            await create_subscription(
                session,
                user_id=user.id,
                lemon_id=lemon_id,
                status=status or "on_trial",
                plan=plan,
                renews_at=renews_at,
                ends_at=ends_at,
            )
        return {"ok": True}

    elif event in {"subscription_payment_success", "subscription_updated"}:
        if not lemon_id:
            return {"ok": True}
        existing = await get_subscription_by_lemon_id(session, lemon_id)
        if existing:
            await update_subscription(
                session,
                existing.id,
                status="active" if event == "subscription_payment_success" else (status or existing.status),
                plan=plan or existing.plan,
                renews_at=renews_at,
                ends_at=ends_at,
            )
        return {"ok": True}

    elif event in {"subscription_canceled", "subscription_expired"}:
        if not lemon_id:
            return {"ok": True}
        existing = await get_subscription_by_lemon_id(session, lemon_id)
        if existing:
            await update_subscription(
                session,
                existing.id,
                status="canceled" if event == "subscription_canceled" else "expired",
                renews_at=renews_at,
                ends_at=ends_at,
            )
        return {"ok": True}

    return {"ok": True}



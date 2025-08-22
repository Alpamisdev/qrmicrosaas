from __future__ import annotations

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import os
import httpx

from app.db import get_async_session
from app.crud_user import get_user_by_id
from app.crud_subscription import (
    get_latest_subscription_for_user,
)


router = APIRouter()


LEMON_MONTHLY_URL = "https://qrworld.lemonsqueezy.com/buy/513ea8a6-2af5-439d-a606-0793622a43bd"
LEMON_YEARLY_URL = "https://qrworld.lemonsqueezy.com/buy/59118d16-8fdf-4972-aa85-2b79bcc856ee"


def _append_custom_data(url: str, user_id: int) -> str:
    # Add multiple forms to maximize compatibility with Lemon Squeezy buy links
    #  - custom[user_id]
    #  - custom_data[user_id]
    #  - checkout[custom][user_id]
    from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

    u = urlparse(url)
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    q.update({
        "custom[user_id]": str(user_id),
        "custom_data[user_id]": str(user_id),
        "checkout[custom][user_id]": str(user_id),
    })
    new_query = urlencode(q)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))


@router.get("/pricing")
async def pricing(request: Request, session: AsyncSession = Depends(get_async_session)):
    # Build checkout links if user logged in so we can attach user id
    user_id = request.session.get("user_id")
    monthly = LEMON_MONTHLY_URL
    yearly = LEMON_YEARLY_URL
    if user_id:
        monthly = _append_custom_data(monthly, int(user_id))
        yearly = _append_custom_data(yearly, int(user_id))
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "pricing.html",
        {
            "request": request,
            "monthly_url": monthly,
            "yearly_url": yearly,
        },
    )


@router.post("/cancel-subscription")
async def cancel_subscription(request: Request, session: AsyncSession = Depends(get_async_session)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login")
    user = await get_user_by_id(session, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sub = await get_latest_subscription_for_user(session, user.id)
    if not sub or not sub.lemon_id:
        raise HTTPException(status_code=400, detail="No active Lemon subscription found")

    api_key = os.getenv("LEMON_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Lemon API key not configured")

    url = f"https://api.lemonsqueezy.com/v1/subscriptions/{sub.lemon_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(url, headers=headers)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Lemon API error: {e}")

    # Webhook will update status, we simply redirect back
    return RedirectResponse("/dashboard", status_code=302)



from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud_dynamic_qr import (
    create_dynamic_qr,
    get_qr_by_short_code,
    list_user_qrs,
    update_qr_destination,
    record_scan,
    list_qr_scans,
)
from typing import Optional
from collections import Counter
from datetime import datetime
import json
from time import monotonic
import secrets
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Base URL for constructing absolute short links
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://qrgenerator.world").rstrip("/")


def get_user_id(request: Request) -> Optional[int]:
    user_id = request.session.get("user_id")
    return int(user_id) if user_id else None


# Simple in-memory de-duplication for rapid repeat hits (e.g., browser double-fetch)
_RECENT_SCANS: dict[str, float] = {}
_RECENT_SCAN_TTL_SECONDS = 5.0

def _should_record_scan(key: str) -> bool:
    now = monotonic()
    last = _RECENT_SCANS.get(key)
    if last is not None and (now - last) < _RECENT_SCAN_TTL_SECONDS:
        return False
    _RECENT_SCANS[key] = now
    # Opportunistic cleanup
    if len(_RECENT_SCANS) > 10000:
        expired = [k for k, t in _RECENT_SCANS.items() if (now - t) >= _RECENT_SCAN_TTL_SECONDS]
        for k in expired:
            _RECENT_SCANS.pop(k, None)
    return True


def generate_short_code() -> str:
    return secrets.token_urlsafe(6)[:8]


def _detect_device_os_browser(user_agent: str) -> tuple[str, Optional[str], Optional[str]]:
    ua = user_agent.lower()
    # Device
    device = "mobile" if any(x in ua for x in ["mobile", "iphone", "android", "ipod"]) else ("tablet" if any(x in ua for x in ["ipad", "tablet"]) else "desktop")
    # OS
    if "android" in ua:
        os = "android"
    elif any(x in ua for x in ["iphone", "ipad", "ipod", "ios"]):
        os = "ios"
    elif "windows" in ua:
        os = "windows"
    elif "mac os x" in ua or "macintosh" in ua:
        os = "macos"
    elif "cros" in ua:
        os = "chromeos"
    elif "linux" in ua:
        os = "linux"
    else:
        os = None
    # Browser (order matters)
    if "yabrowser" in ua or "yandex" in ua:
        browser = "yandex"
    elif "opr/" in ua or "opera" in ua:
        browser = "opera"
    elif "edg/" in ua or "edge" in ua:
        browser = "edge"
    elif "samsungbrowser" in ua:
        browser = "samsung"
    elif "firefox" in ua or "fxios" in ua:
        browser = "firefox"
    elif "crios" in ua:
        browser = "chrome"
    elif "chrome" in ua and "chromium" not in ua and "edg" not in ua and "opr" not in ua and "yabrowser" not in ua:
        browser = "chrome"
    elif "safari" in ua:
        browser = "safari"
    elif "brave" in ua:
        browser = "brave"
    else:
        browser = None
    return device, os, browser


@router.get("/d/new", response_class=HTMLResponse)
async def new_dynamic_qr(request: Request):
    if not get_user_id(request):
        return RedirectResponse("/auth/login", status_code=307)
    return templates.TemplateResponse("dynamic_qr/new.html", {"request": request})


@router.post("/d/create", response_class=HTMLResponse)
async def create_dynamic_qr_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    user_id = get_user_id(request)
    if not user_id:
        return RedirectResponse("/auth/login", status_code=307)
    form = await request.form()
    destination_url = str(form.get("destination_url") or "").strip()
    title = str(form.get("title") or "").strip()
    if not destination_url:
        return templates.TemplateResponse(
            "dynamic_qr/new.html",
            {"request": request, "error": "Destination URL is required", "title": title, "destination_url": destination_url},
            status_code=400,
        )

    # Ensure unique short code
    for _ in range(5):
        short_code = generate_short_code()
        existing = await get_qr_by_short_code(session, short_code)
        if not existing:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate unique short link")

    qr = await create_dynamic_qr(session, user_id=user_id, short_code=short_code, destination_url=destination_url, title=title or None)
    return RedirectResponse(f"/d/{qr.short_code}", status_code=302)


@router.get("/d/{short_code}", response_class=HTMLResponse)
async def view_dynamic_qr(request: Request, short_code: str, session: AsyncSession = Depends(get_async_session)):
    user_id = get_user_id(request)
    if not user_id:
        return RedirectResponse("/auth/login", status_code=307)
    qr = await get_qr_by_short_code(session, short_code)
    if not qr or qr.user_id != user_id:
        raise HTTPException(status_code=404, detail="QR not found")
    scans = await list_qr_scans(session, qr.id)

    # Build stats for charts
    device_counts = Counter((s.device or "unknown").lower() for s in scans)
    browser_counts = Counter((s.browser or "unknown").lower() for s in scans)
    os_counts = Counter((s.os or "unknown").lower() for s in scans)
    # Group by day
    date_counts: dict[str, int] = {}
    for s in scans:
        try:
            d = s.scanned_at.date().isoformat() if isinstance(s.scanned_at, datetime) else str(s.scanned_at).split(" ")[0]
        except Exception:
            d = "unknown"
        date_counts[d] = date_counts.get(d, 0) + 1

    def pack_counts(counter: Counter) -> dict:
        labels = list(counter.keys())
        data = [counter[k] for k in labels]
        return {"labels": labels, "data": data}

    stats = {
        "total": len(scans),
        "devices": pack_counts(device_counts),
        "browsers": pack_counts(browser_counts),
        "oses": pack_counts(os_counts),
        "dates": {"labels": sorted(date_counts.keys()), "data": [date_counts[k] for k in sorted(date_counts.keys())]},
    }

    return templates.TemplateResponse(
        "dynamic_qr/show.html",
        {
            "request": request,
            "qr": qr,
            "scans": scans,
            "stats_json": json.dumps(stats),
            "short_url": f"{APP_BASE_URL}/r/{qr.short_code}",
        },
    )


@router.post("/d/{short_code}/update")
async def update_dynamic_qr(request: Request, short_code: str, session: AsyncSession = Depends(get_async_session)):
    user_id = get_user_id(request)
    if not user_id:
        return RedirectResponse("/auth/login", status_code=307)
    form = await request.form()
    destination_url = str(form.get("destination_url") or "").strip()
    if not destination_url:
        raise HTTPException(status_code=400, detail="Destination URL is required")
    qr = await get_qr_by_short_code(session, short_code)
    if not qr or qr.user_id != user_id:
        raise HTTPException(status_code=404, detail="QR not found")
    await update_qr_destination(session, qr.id, destination_url)
    return RedirectResponse(f"/d/{short_code}", status_code=302)


@router.get("/my/dynamic", response_class=HTMLResponse)
async def my_dynamic_qrs(request: Request, session: AsyncSession = Depends(get_async_session)):
    user_id = get_user_id(request)
    if not user_id:
        return RedirectResponse("/auth/login", status_code=307)
    qrs = await list_user_qrs(session, user_id)
    return templates.TemplateResponse("dynamic_qr/list.html", {"request": request, "qrs": qrs})


@router.get("/r/{short_code}")
async def redirect_short(request: Request, short_code: str, session: AsyncSession = Depends(get_async_session)):
    qr = await get_qr_by_short_code(session, short_code)
    if not qr:
        raise HTTPException(status_code=404, detail="Link not found")

    # Parse user agent for device / OS / browser (including Yandex)
    ua = request.headers.get("user-agent", "")
    device, os, browser = _detect_device_os_browser(ua)

    # Basic geo via headers (a reverse proxy like Cloudflare can inject these)
    country = request.headers.get("cf-ipcountry") or request.headers.get("x-country") or None
    city = request.headers.get("x-city") or None
    region = request.headers.get("x-region") or None

    # De-duplicate rapid repeat requests from same client
    # Better public client IP detection (proxies/CDNs)
    ip = request.headers.get("cf-connecting-ip") or request.headers.get("true-client-ip") or request.headers.get("x-real-ip") or request.headers.get("x-client-ip") or request.headers.get("fastly-client-ip")
    if not ip:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            ip = xff.split(",")[0].strip()
    if not ip:
        fwd = request.headers.get("forwarded")
        if fwd:
            # e.g. Forwarded: for=203.0.113.43;proto=https;by=203.0.113.43
            try:
                parts = [p.strip() for p in fwd.split(";")]
                for part in parts:
                    if part.lower().startswith("for="):
                        val = part.split("=", 1)[1].strip().strip('"')
                        # strip possible port
                        if val.startswith("[") and "]" in val:
                            val = val[1:val.index("]")]
                        if ":" in val:
                            val = val.split(":")[0]
                        ip = val
                        break
            except Exception:
                pass
    if not ip:
        ip = request.client.host if request.client else ""
    fingerprint = f"{short_code}:{ip}:{ua[:64]}"
    if _should_record_scan(fingerprint):
        await record_scan(
            session,
            qr_id=qr.id,
            ip=ip,
            country=country,
            region=region,
            city=city,
            user_agent=ua,
            device=device,
            os=os,
            browser=browser,
            referrer=request.headers.get("referer"),
        )

    return RedirectResponse(qr.destination_url, status_code=302)


@router.post("/api/d/create")
async def api_create_dynamic_qr(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_async_session),
):
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    destination_url = str(payload.get("destination_url") or "").strip()
    title = str(payload.get("title") or "").strip() or None
    if not destination_url:
        raise HTTPException(status_code=422, detail="destination_url is required")

    # Ensure unique short code
    for _ in range(5):
        short_code = generate_short_code()
        existing = await get_qr_by_short_code(session, short_code)
        if not existing:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate unique short link")

    qr = await create_dynamic_qr(
        session, user_id=user_id, short_code=short_code, destination_url=destination_url, title=title
    )
    return {
        "short_code": qr.short_code,
        "redirect_url": f"/r/{qr.short_code}",
        "absolute_redirect_url": f"{APP_BASE_URL}/r/{qr.short_code}",
    }



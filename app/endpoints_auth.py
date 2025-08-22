from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

from app.db import get_async_session
from app.crud_user import (
    create_user,
    get_user_by_google_id,
    get_user_by_email,
    get_user_by_id,
)


load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Base URL of the application, used to construct absolute URLs in production
# Defaults to the public domain for deployment but can be overridden for local dev
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://qrgenerator.world").rstrip("/")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Prefer explicit GOOGLE_REDIRECT_URI if provided, otherwise build from APP_BASE_URL
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI") or f"{APP_BASE_URL}/auth/google/callback"


@router.get("/auth/login")
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/auth/google")
async def start_google_oauth():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str, session: AsyncSession = Depends(get_async_session)):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }

    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(token_url, data=token_data)
            token_resp.raise_for_status()
            tokens = token_resp.json()
            access_token = tokens.get("access_token")

            if not access_token:
                raise HTTPException(status_code=400, detail="Failed to obtain access token")

            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_resp = await client.get(userinfo_url, headers=headers)
            user_resp.raise_for_status()
            info = user_resp.json()

        # Persist or update user
        user = await get_user_by_google_id(session, info["id"])  # type: ignore[index]
        if not user:
            user = await get_user_by_email(session, info["email"])  # type: ignore[index]
            if user:
                await session.refresh(user)
                setattr(user, "google_id", info["id"])  # type: ignore[index]
                setattr(user, "name", info.get("name"))
                setattr(user, "picture", info.get("picture"))
                await session.commit()
                await session.refresh(user)
            else:
                user = await create_user(
                    session,
                    {
                        "email": info["email"],
                        "google_id": info["id"],
                        "name": info.get("name"),
                        "picture": info.get("picture"),
                    },
                )

        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        return RedirectResponse("/dashboard", status_code=302)

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Google API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {e}")


@router.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@router.get("/dashboard")
async def dashboard(request: Request, session: AsyncSession = Depends(get_async_session)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login")
    user = await get_user_by_id(session, int(user_id))
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@router.get("/profile")
async def profile(request: Request, session: AsyncSession = Depends(get_async_session)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/auth/login")
    user = await get_user_by_id(session, int(user_id))
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})



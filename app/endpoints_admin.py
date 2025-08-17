from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_admin import (
    create_admin, get_admin, get_all_admins, update_admin, delete_admin
)
from app.models import Admin
from typing import List
from pydantic import BaseModel
from app.db import get_async_session, AsyncSessionLocal
from app.crud_user import count_users, count_users_since, list_recent_users, list_users_since
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/admins", tags=["admins"])

class AdminCreate(BaseModel):
    username: str
    password_hash: str

class AdminOut(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

@router.post("/", response_model=AdminOut)
async def create_admin_view(data: AdminCreate, session: AsyncSession = Depends(get_async_session)):
    admin = await create_admin(session, data.username, data.password_hash)
    return admin

@router.get("/", response_model=List[AdminOut])
async def list_admins(session: AsyncSession = Depends(get_async_session)):
    admins = await get_all_admins(session)
    return admins

@router.get("/{admin_id}", response_model=AdminOut)
async def get_admin_view(admin_id: int, session: AsyncSession = Depends(get_async_session)):
    admin = await get_admin(session, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

@router.put("/{admin_id}", response_model=AdminOut)
async def update_admin_view(admin_id: int, data: AdminCreate, session: AsyncSession = Depends(get_async_session)):
    admin = await update_admin(session, admin_id, username=data.username, password_hash=data.password_hash)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

@router.delete("/{admin_id}")
async def delete_admin_view(admin_id: int, session: AsyncSession = Depends(get_async_session)):
    success = await delete_admin(session, admin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {"ok": True} 


@router.get("/admin/users", tags=["admins"])
async def admin_users_stats(request: Request):
    # Require admin session
    admin_id = request.session.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    async with AsyncSessionLocal() as session:
        total = await count_users(session)
        last_7_days = await count_users_since(session, datetime.utcnow() - timedelta(days=7))
        recent = await list_recent_users(session, limit=50)
        last_30_list = await list_users_since(session, datetime.utcnow() - timedelta(days=30))
    return templates.TemplateResponse(
        "admin/users_stats.html",
        {
            "request": request,
            "total": total,
            "last_7_days": last_7_days,
            "recent": recent,
            "last_30": last_30_list,
        },
    )
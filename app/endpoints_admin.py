from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_admin import (
    create_admin, get_admin, get_all_admins, update_admin, delete_admin
)
from app.models import Admin
from typing import List
from pydantic import BaseModel
from app.db import get_async_session

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
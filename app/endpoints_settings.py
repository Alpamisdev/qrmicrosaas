from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_settings import (
    create_settings, get_settings, get_all_settings, update_settings, delete_settings
)
from app.models import SiteSettings
from typing import List, Optional
from pydantic import BaseModel
from app.db import get_async_session

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsCreate(BaseModel):
    site_name: str
    google_analytics_code: Optional[str] = None
    ad_block_code: Optional[str] = None

class SettingsOut(BaseModel):
    id: int
    site_name: str
    google_analytics_code: Optional[str]
    ad_block_code: Optional[str]
    class Config:
        from_attributes = True

@router.post("/", response_model=SettingsOut)
async def create_settings_view(data: SettingsCreate, session: AsyncSession = Depends(get_async_session)):
    settings = await create_settings(session, **data.dict())
    return settings

@router.get("/", response_model=List[SettingsOut])
async def list_settings(session: AsyncSession = Depends(get_async_session)):
    settings = await get_all_settings(session)
    return settings

@router.get("/{settings_id}", response_model=SettingsOut)
async def get_settings_view(settings_id: int, session: AsyncSession = Depends(get_async_session)):
    settings = await get_settings(session, settings_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@router.put("/{settings_id}", response_model=SettingsOut)
async def update_settings_view(settings_id: int, data: SettingsCreate, session: AsyncSession = Depends(get_async_session)):
    settings = await update_settings(session, settings_id, **data.dict())
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@router.delete("/{settings_id}")
async def delete_settings_view(settings_id: int, session: AsyncSession = Depends(get_async_session)):
    success = await delete_settings(session, settings_id)
    if not success:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {"ok": True} 
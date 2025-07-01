from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_tag import (
    create_tag, get_tag, get_all_tags, update_tag, delete_tag
)
from app.models import Tag
from typing import List
from pydantic import BaseModel
from app.db import get_async_session

router = APIRouter(prefix="/tags", tags=["tags"])

class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

@router.post("/", response_model=TagOut)
async def create_tag_view(data: TagCreate, session: AsyncSession = Depends(get_async_session)):
    tag = await create_tag(session, data.name)
    return tag

@router.get("/", response_model=List[TagOut])
async def list_tags(session: AsyncSession = Depends(get_async_session)):
    tags = await get_all_tags(session)
    return tags

@router.get("/{tag_id}", response_model=TagOut)
async def get_tag_view(tag_id: int, session: AsyncSession = Depends(get_async_session)):
    tag = await get_tag(session, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/{tag_id}", response_model=TagOut)
async def update_tag_view(tag_id: int, data: TagCreate, session: AsyncSession = Depends(get_async_session)):
    tag = await update_tag(session, tag_id, name=data.name)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.delete("/{tag_id}")
async def delete_tag_view(tag_id: int, session: AsyncSession = Depends(get_async_session)):
    success = await delete_tag(session, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"ok": True} 
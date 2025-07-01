from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_category import (
    create_category, get_category, get_all_categories, update_category, delete_category
)
from app.models import Category
from typing import List
from pydantic import BaseModel
from app.db import get_async_session

router = APIRouter(prefix="/categories", tags=["categories"])

class CategoryCreate(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

@router.post("/", response_model=CategoryOut)
async def create_category_view(data: CategoryCreate, session: AsyncSession = Depends(get_async_session)):
    category = await create_category(session, data.name)
    return category

@router.get("/", response_model=List[CategoryOut])
async def list_categories(session: AsyncSession = Depends(get_async_session)):
    categories = await get_all_categories(session)
    return categories

@router.get("/{category_id}", response_model=CategoryOut)
async def get_category_view(category_id: int, session: AsyncSession = Depends(get_async_session)):
    category = await get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryOut)
async def update_category_view(category_id: int, data: CategoryCreate, session: AsyncSession = Depends(get_async_session)):
    category = await update_category(session, category_id, name=data.name)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.delete("/{category_id}")
async def delete_category_view(category_id: int, session: AsyncSession = Depends(get_async_session)):
    success = await delete_category(session, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"ok": True} 
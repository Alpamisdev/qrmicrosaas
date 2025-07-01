from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_post import (
    create_post, get_post, get_post_by_slug, get_all_posts, update_post, delete_post
)
from app.models import Post, PostStatus
from typing import List, Optional
from pydantic import BaseModel
from app.db import get_async_session

router = APIRouter(prefix="/posts", tags=["posts"])

class PostCreate(BaseModel):
    title: str
    slug: str
    excerpt: str
    content: str
    status: PostStatus
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

class PostOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str
    content: str
    status: PostStatus
    category_id: Optional[int]
    tag_ids: List[int] = []
    seo_title: Optional[str]
    seo_description: Optional[str]
    class Config:
        from_attributes = True

@router.post("/", response_model=PostOut)
async def create_post_view(data: PostCreate, session: AsyncSession = Depends(get_async_session)):
    post = await create_post(session, **data.dict())
    return PostOut(
        **post.__dict__,
        tag_ids=[tag.id for tag in post.tags] if post.tags else [],
        category_id=post.category_id
    )

@router.get("/", response_model=List[PostOut])
async def list_posts(session: AsyncSession = Depends(get_async_session)):
    posts = await get_all_posts(session)
    return [PostOut(
        **post.__dict__,
        tag_ids=[tag.id for tag in post.tags] if post.tags else [],
        category_id=post.category_id
    ) for post in posts]

@router.get("/{post_id}", response_model=PostOut)
async def get_post_view(post_id: int, session: AsyncSession = Depends(get_async_session)):
    post = await get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut(
        **post.__dict__,
        tag_ids=[tag.id for tag in post.tags] if post.tags else [],
        category_id=post.category_id
    )

@router.get("/slug/{slug}", response_model=PostOut)
async def get_post_by_slug_view(slug: str, session: AsyncSession = Depends(get_async_session)):
    post = await get_post_by_slug(session, slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut(
        **post.__dict__,
        tag_ids=[tag.id for tag in post.tags] if post.tags else [],
        category_id=post.category_id
    )

@router.put("/{post_id}", response_model=PostOut)
async def update_post_view(post_id: int, data: PostCreate, session: AsyncSession = Depends(get_async_session)):
    post = await update_post(session, post_id, **data.dict())
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut(
        **post.__dict__,
        tag_ids=[tag.id for tag in post.tags] if post.tags else [],
        category_id=post.category_id
    )

@router.delete("/{post_id}")
async def delete_post_view(post_id: int, session: AsyncSession = Depends(get_async_session)):
    success = await delete_post(session, post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True} 
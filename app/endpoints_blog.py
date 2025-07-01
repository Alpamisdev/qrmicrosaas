from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db import get_async_session
from app.crud_post import get_all_posts, get_post_by_slug
from app.crud_tag import get_all_tags
from app.crud_category import get_all_categories
from app.models import PostStatus
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request, session: AsyncSession = Depends(get_async_session), tag: str = Query(None), category: str = Query(None)):
    posts = [
        p for p in await get_all_posts(session)
        if p.status == PostStatus.published and not getattr(p, 'is_deleted', False)
    ]
    selected_tag = None
    selected_category = None
    if tag:
        # Find tag by slug or name
        tags = await get_all_tags(session)
        selected_tag = next((t for t in tags if getattr(t, 'slug', None) == tag or t.name == tag), None)
        if selected_tag:
            posts = [p for p in posts if selected_tag in p.tags]
    if category:
        # Find category by slug or name
        categories = await get_all_categories(session)
        selected_category = next((c for c in categories if getattr(c, 'slug', None) == category or c.name == category), None)
        if selected_category:
            posts = [p for p in posts if p.category and p.category.id == selected_category.id]
    posts.sort(key=lambda p: getattr(p, 'created_at', None) or 0, reverse=True)
    return templates.TemplateResponse("blog_list.html", {"request": request, "posts": posts, "selected_tag": selected_tag, "selected_category": selected_category})

@router.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_single(request: Request, slug: str, session: AsyncSession = Depends(get_async_session)):
    post = await get_post_by_slug(session, slug)
    if not post or post.status != PostStatus.published or getattr(post, 'is_deleted', False):
        return RedirectResponse("/blog")
    return templates.TemplateResponse("single_post.html", {"request": request, "post": post}) 
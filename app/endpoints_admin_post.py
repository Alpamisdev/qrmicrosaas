from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud_post import create_post, get_all_posts, get_post, update_post
from app.crud_category import get_all_categories
from app.models import PostStatus
from fastapi.templating import Jinja2Templates
import re
from app.crud_tag import get_all_tags
from app.utils.markdown import convert_markdown_to_html
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class PreviewRequest(BaseModel):
    content: str

def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'-+', '-', value)
    return value.strip('-')

@router.get("/admin/posts/new", response_class=HTMLResponse)
async def admin_post_form(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    categories = await get_all_categories(session)
    tags = await get_all_tags(session)
    posts = [p for p in await get_all_posts(session) if not p.is_deleted]
    return templates.TemplateResponse("admin/post_form.html", {"request": request, "categories": categories, "tags": tags, "post": None, "posts": posts})

@router.get("/admin/posts/edit/{post_id}", response_class=HTMLResponse)
async def admin_post_edit(request: Request, post_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    categories = await get_all_categories(session)
    tags = await get_all_tags(session)
    post = await get_post(session, post_id)
    posts = [p for p in await get_all_posts(session) if not p.is_deleted]
    return templates.TemplateResponse("admin/post_form.html", {"request": request, "categories": categories, "tags": tags, "post": post, "posts": posts})

@router.post("/admin/posts/save", response_class=HTMLResponse)
async def admin_post_save(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    form = await request.form()
    post_id = form.get("post_id")
    post_id_str = str(post_id) if post_id is not None else ""
    title = str(form.get("title") or "")
    slug = str(form.get("slug") or "")
    if not slug:
        slug = slugify(title)
    content = str(form.get("content") or "")
    category_id_raw = form.get("category_id")
    category_id_str = str(category_id_raw) if category_id_raw is not None else ""
    category_id = int(category_id_str) if category_id_str.isdigit() else None
    # Parse tags as a list of IDs
    tag_ids = form.getlist("tags")
    tag_ids = [int(tid) for tid in tag_ids if isinstance(tid, str) and tid.isdigit()]
    if post_id_str.isdigit():
        # Update existing post
        await update_post(
            session,
            int(post_id_str),
            title=title,
            slug=slug,
            excerpt=content[:150],
            content=content,
            category_id=category_id,
            tag_ids=tag_ids,
            # status, seo_title, seo_description can be added as needed
        )
    else:
        # Create new post
        await create_post(
            session,
            title=title,
            slug=slug,
            excerpt=content[:150],
            content=content,
            status=PostStatus.published,
            category_id=category_id,
            tag_ids=tag_ids,
            seo_title=None,
            seo_description=None,
        )
    return RedirectResponse("/admin/posts/new", status_code=302)

@router.post("/admin/posts/delete/{post_id}", response_class=HTMLResponse)
async def admin_post_delete(request: Request, post_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    await update_post(session, post_id, is_deleted=True)
    return RedirectResponse("/admin/posts/new", status_code=302)

@router.post("/admin/posts/preview", response_class=HTMLResponse)
async def preview_post(request: PreviewRequest):
    """Preview Markdown content as HTML"""
    html = convert_markdown_to_html(request.content)
    return f'<div class="prose prose-lg max-w-none prose-headings:font-bold prose-a:text-blue-600 prose-code:bg-gray-100 prose-code:p-0.5 prose-code:rounded prose-pre:bg-gray-800 prose-pre:text-gray-100">{html}</div>' 
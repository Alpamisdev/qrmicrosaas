from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud_tag import get_all_tags, get_tag, create_tag, update_tag, delete_tag
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/tags", response_class=HTMLResponse)
async def admin_tag_form(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    tags = await get_all_tags(session)
    return templates.TemplateResponse("admin/tag_form.html", {"request": request, "tags": tags, "tag": None})

@router.get("/admin/tags/edit/{tag_id}", response_class=HTMLResponse)
async def admin_tag_edit(request: Request, tag_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    tags = await get_all_tags(session)
    tag = await get_tag(session, tag_id)
    return templates.TemplateResponse("admin/tag_form.html", {"request": request, "tags": tags, "tag": tag})

@router.post("/admin/tags/save", response_class=HTMLResponse)
async def admin_tag_save(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    form = await request.form()
    tag_id = form.get("tag_id")
    tag_id_str = str(tag_id) if tag_id is not None else ""
    name = str(form.get("name") or "")
    if tag_id_str.isdigit():
        await update_tag(session, int(tag_id_str), name=name)
    else:
        await create_tag(session, name)
    return RedirectResponse("/admin/tags", status_code=302)

@router.post("/admin/tags/delete/{tag_id}", response_class=HTMLResponse)
async def admin_tag_delete(request: Request, tag_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    await delete_tag(session, tag_id)
    return RedirectResponse("/admin/tags", status_code=302) 
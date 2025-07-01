from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud_category import get_all_categories, get_category, create_category, update_category, delete_category
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/categories", response_class=HTMLResponse)
async def admin_category_form(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    categories = await get_all_categories(session)
    return templates.TemplateResponse("admin/category.html", {"request": request, "categories": categories, "category": None})

@router.get("/admin/categories/edit/{category_id}", response_class=HTMLResponse)
async def admin_category_edit(request: Request, category_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    categories = await get_all_categories(session)
    category = await get_category(session, category_id)
    return templates.TemplateResponse("admin/category.html", {"request": request, "categories": categories, "category": category})

@router.post("/admin/categories/save", response_class=HTMLResponse)
async def admin_category_save(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    form = await request.form()
    category_id = form.get("category_id")
    category_id_str = str(category_id) if category_id is not None else ""
    name = str(form.get("name") or "")
    if category_id_str.isdigit():
        await update_category(session, int(category_id_str), name=name)
    else:
        await create_category(session, name)
    return RedirectResponse("/admin/categories", status_code=302)

@router.post("/admin/categories/delete/{category_id}", response_class=HTMLResponse)
async def admin_category_delete(request: Request, category_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    await delete_category(session, category_id)
    return RedirectResponse("/admin/categories", status_code=302) 
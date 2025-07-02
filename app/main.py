from fastapi import FastAPI, Request, status, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.crud_admin import get_admin_by_username
from app.db import get_async_session
from passlib.context import CryptContext
from app.endpoints_admin import router as admin_router
from app.endpoints_tag import router as tag_router
from app.endpoints_category import router as category_router
from app.endpoints_post import router as post_router
from app.endpoints_settings import router as settings_router
from app.endpoints_seo import router as seo_router
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud_post import create_post, get_all_posts, get_post, update_post, delete_post
from app.crud_category import get_all_categories
from app.models import PostStatus
from app.endpoints_admin_post import router as admin_post_router
from app.endpoints_admin_category import router as admin_category_router
from app.endpoints_admin_tag import router as admin_tag_router
from app.endpoints_blog import router as blog_router

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(admin_router)
app.include_router(tag_router)
app.include_router(category_router)
app.include_router(post_router)
app.include_router(settings_router)
app.include_router(admin_post_router)
app.include_router(admin_category_router)
app.include_router(admin_tag_router)
app.include_router(blog_router)
app.include_router(seo_router)

templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    return templates.TemplateResponse("blog_list.html", {"request": request})

@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    raise exc

@app.get("/qradmin")
async def qradmin_redirect():
    return RedirectResponse("/admin/login")

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_get(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_async_session)):
    admin = await get_admin_by_username(session, username)
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse("admin/login.html", {"request": request, "error": "Invalid username or password."})
    request.session["admin_id"] = admin.id
    return RedirectResponse("/admin/dashboard", status_code=302)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)

@app.get("/admin/posts/new", response_class=HTMLResponse)
async def admin_post_form(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    categories = await get_all_categories(session)
    posts = [p for p in await get_all_posts(session) if not p.is_deleted]
    return templates.TemplateResponse("admin/post_form.html", {"request": request, "categories": categories, "post": None, "posts": posts})

@app.get("/admin/posts/edit/{post_id}", response_class=HTMLResponse)
async def admin_post_edit(request: Request, post_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    categories = await get_all_categories(session)
    post = await get_post(session, post_id)
    posts = [p for p in await get_all_posts(session) if not p.is_deleted]
    return templates.TemplateResponse("admin/post_form.html", {"request": request, "categories": categories, "post": post, "posts": posts})

@app.post("/admin/posts/save", response_class=HTMLResponse)
async def admin_post_save(request: Request, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    form = await request.form()
    post_id = form.get("post_id")
    post_id_str = str(post_id) if post_id is not None else ""
    title = str(form.get("title") or "")
    slug = str(form.get("slug") or "")
    content = str(form.get("content") or "")
    category_id_raw = form.get("category_id")
    category_id_str = str(category_id_raw) if category_id_raw is not None else ""
    category_id = int(category_id_str) if category_id_str.isdigit() else None
    tags_raw = str(form.get("tags") or "")
    tag_names = [t.strip() for t in tags_raw.split(",") if t.strip()]
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
            # tag_ids=[],
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
            tag_ids=[],
            seo_title=None,
            seo_description=None,
        )
    return RedirectResponse("/admin/posts/new", status_code=302)

@app.post("/admin/posts/delete/{post_id}", response_class=HTMLResponse)
async def admin_post_delete(request: Request, post_id: int, session: AsyncSession = Depends(get_async_session)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return RedirectResponse("/admin/login")
    await update_post(session, post_id, is_deleted=True)
    return RedirectResponse("/admin/posts/new", status_code=302)

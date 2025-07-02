from fastapi import APIRouter, Request, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.crud_post import get_all_posts
from app.models import PostStatus
from datetime import datetime

router = APIRouter()

@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /settings/

Sitemap: https://qrgenerator.world/sitemap.xml"""

@router.get("/sitemap.xml")
async def sitemap(request: Request, session: AsyncSession = Depends(get_async_session)):
    # Get all published blog posts
    posts = await get_all_posts(session)
    published_posts = [post for post in posts if post.status == PostStatus.published and not post.is_deleted]
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://qrgenerator.world/</loc>
        <priority>1.0</priority>
        <changefreq>daily</changefreq>
        <lastmod>{current_date}</lastmod>
    </url>
    <url>
        <loc>https://qrgenerator.world/blog</loc>
        <priority>0.8</priority>
        <changefreq>weekly</changefreq>
        <lastmod>{current_date}</lastmod>
    </url>
    <url>
        <loc>https://qrgenerator.world/privacy</loc>
        <priority>0.3</priority>
        <changefreq>yearly</changefreq>
        <lastmod>{current_date}</lastmod>
    </url>"""

    # Add blog posts to sitemap
    for post in published_posts:
        post_date = str(post.created_at).split()[0] if post.created_at else current_date
        post_entry = f"""
    <url>
        <loc>https://qrgenerator.world/blog/{post.slug}</loc>
        <priority>0.7</priority>
        <changefreq>monthly</changefreq>
        <lastmod>{post_date}</lastmod>
    </url>"""
        xml_content += post_entry

    xml_content += "\n</urlset>"
    return Response(content=xml_content, media_type="application/xml") 
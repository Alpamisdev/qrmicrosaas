from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models import Post, Tag, Category, PostStatus
from typing import List, Optional

async def create_post(session: AsyncSession, title: str, slug: str, excerpt: str, content: str, status: PostStatus, category_id: Optional[int] = None, tag_ids: Optional[List[int]] = None, seo_title: Optional[str] = None, seo_description: Optional[str] = None) -> Post:
    post = Post(
        title=title,
        slug=slug,
        excerpt=excerpt,
        content=content,
        status=status,
        category_id=category_id,
        seo_title=seo_title,
        seo_description=seo_description,
    )
    if tag_ids:
        tags = await session.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        post.tags = list(tags.scalars().all())
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post

async def get_post(session: AsyncSession, post_id: int) -> Optional[Post]:
    result = await session.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()

async def get_post_by_slug(session: AsyncSession, slug: str) -> Optional[Post]:
    result = await session.execute(
        select(Post)
        .where(Post.slug == slug)
        .options(
            selectinload(Post.category),
            selectinload(Post.tags)
        )
    )
    return result.scalar_one_or_none()

async def get_all_posts(session: AsyncSession) -> List[Post]:
    result = await session.execute(
        select(Post)
        .options(
            selectinload(Post.category),
            selectinload(Post.tags)
        )
    )
    return list(result.scalars().all())

async def update_post(session: AsyncSession, post_id: int, **kwargs) -> Optional[Post]:
    post = await get_post(session, post_id)
    if not post:
        return None
    tag_ids = kwargs.pop('tag_ids', None)
    for key, value in kwargs.items():
        setattr(post, key, value)
    if tag_ids is not None:
        tags = await session.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        post.tags = list(tags.scalars().all())
    await session.commit()
    await session.refresh(post)
    return post

async def delete_post(session: AsyncSession, post_id: int) -> bool:
    post = await get_post(session, post_id)
    if not post:
        return False
    await session.delete(post)
    await session.commit()
    return True 
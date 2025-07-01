from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Tag
from typing import List, Optional

async def create_tag(session: AsyncSession, name: str) -> Tag:
    tag = Tag(name=name)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag

async def get_tag(session: AsyncSession, tag_id: int) -> Optional[Tag]:
    result = await session.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()

async def get_tag_by_name(session: AsyncSession, name: str) -> Optional[Tag]:
    result = await session.execute(select(Tag).where(Tag.name == name))
    return result.scalar_one_or_none()

async def get_all_tags(session: AsyncSession) -> List[Tag]:
    result = await session.execute(select(Tag))
    return list(result.scalars().all())

async def update_tag(session: AsyncSession, tag_id: int, **kwargs) -> Optional[Tag]:
    tag = await get_tag(session, tag_id)
    if not tag:
        return None
    for key, value in kwargs.items():
        setattr(tag, key, value)
    await session.commit()
    await session.refresh(tag)
    return tag

async def delete_tag(session: AsyncSession, tag_id: int) -> bool:
    tag = await get_tag(session, tag_id)
    if not tag:
        return False
    await session.delete(tag)
    await session.commit()
    return True 
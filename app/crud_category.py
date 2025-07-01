from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Category
from typing import List, Optional

async def create_category(session: AsyncSession, name: str) -> Category:
    category = Category(name=name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category

async def get_category(session: AsyncSession, category_id: int) -> Optional[Category]:
    result = await session.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()

async def get_category_by_name(session: AsyncSession, name: str) -> Optional[Category]:
    result = await session.execute(select(Category).where(Category.name == name))
    return result.scalar_one_or_none()

async def get_all_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category))
    return list(result.scalars().all())

async def update_category(session: AsyncSession, category_id: int, **kwargs) -> Optional[Category]:
    category = await get_category(session, category_id)
    if not category:
        return None
    for key, value in kwargs.items():
        setattr(category, key, value)
    await session.commit()
    await session.refresh(category)
    return category

async def delete_category(session: AsyncSession, category_id: int) -> bool:
    category = await get_category(session, category_id)
    if not category:
        return False
    await session.delete(category)
    await session.commit()
    return True 
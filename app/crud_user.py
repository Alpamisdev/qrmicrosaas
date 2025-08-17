from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, Dict, Any

from app.models import User


async def create_user(session: AsyncSession, user_data: Dict[str, Any]) -> User:
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_google_id(session: AsyncSession, google_id: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def update_user(session: AsyncSession, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return int(result.scalar_one())


async def count_users_since(session: AsyncSession, since_datetime) -> int:
    result = await session.execute(
        select(func.count(User.id)).where(User.created_at >= since_datetime)
    )
    return int(result.scalar_one())


async def list_recent_users(session: AsyncSession, limit: int = 5) -> list[User]:
    result = await session.execute(
        select(User).order_by(desc(User.created_at)).limit(limit)
    )
    return list(result.scalars().all())


async def list_users_since(session: AsyncSession, since_datetime) -> list[User]:
    result = await session.execute(
        select(User).where(User.created_at >= since_datetime).order_by(desc(User.created_at))
    )
    return list(result.scalars().all())



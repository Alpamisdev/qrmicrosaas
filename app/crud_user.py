from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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



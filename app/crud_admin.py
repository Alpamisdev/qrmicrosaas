from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Admin
from typing import List, Optional

async def create_admin(session: AsyncSession, username: str, password_hash: str) -> Admin:
    admin = Admin(username=username, password_hash=password_hash)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin

async def get_admin(session: AsyncSession, admin_id: int) -> Optional[Admin]:
    result = await session.execute(select(Admin).where(Admin.id == admin_id))
    return result.scalar_one_or_none()

async def get_admin_by_username(session: AsyncSession, username: str) -> Optional[Admin]:
    result = await session.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()

async def get_all_admins(session: AsyncSession) -> List[Admin]:
    result = await session.execute(select(Admin))
    return list(result.scalars().all())

async def update_admin(session: AsyncSession, admin_id: int, **kwargs) -> Optional[Admin]:
    admin = await get_admin(session, admin_id)
    if not admin:
        return None
    for key, value in kwargs.items():
        setattr(admin, key, value)
    await session.commit()
    await session.refresh(admin)
    return admin

async def delete_admin(session: AsyncSession, admin_id: int) -> bool:
    admin = await get_admin(session, admin_id)
    if not admin:
        return False
    await session.delete(admin)
    await session.commit()
    return True 
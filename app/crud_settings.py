from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import SiteSettings
from typing import List, Optional

async def create_settings(session: AsyncSession, site_name: str, google_analytics_code: Optional[str] = None, ad_block_code: Optional[str] = None) -> SiteSettings:
    settings = SiteSettings(site_name=site_name, google_analytics_code=google_analytics_code, ad_block_code=ad_block_code)
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings

async def get_settings(session: AsyncSession, settings_id: int) -> Optional[SiteSettings]:
    result = await session.execute(select(SiteSettings).where(SiteSettings.id == settings_id))
    return result.scalar_one_or_none()

async def get_all_settings(session: AsyncSession) -> List[SiteSettings]:
    result = await session.execute(select(SiteSettings))
    return list(result.scalars().all())

async def update_settings(session: AsyncSession, settings_id: int, **kwargs) -> Optional[SiteSettings]:
    settings = await get_settings(session, settings_id)
    if not settings:
        return None
    for key, value in kwargs.items():
        setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return settings

async def delete_settings(session: AsyncSession, settings_id: int) -> bool:
    settings = await get_settings(session, settings_id)
    if not settings:
        return False
    await session.delete(settings)
    await session.commit()
    return True 
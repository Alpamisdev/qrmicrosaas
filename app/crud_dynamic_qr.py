from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models import DynamicQR, QRScan


async def create_dynamic_qr(
    session: AsyncSession,
    user_id: int,
    short_code: str,
    destination_url: str,
    title: Optional[str] = None,
) -> DynamicQR:
    qr = DynamicQR(
        user_id=user_id,
        short_code=short_code,
        destination_url=destination_url,
        title=title,
    )
    session.add(qr)
    await session.commit()
    await session.refresh(qr)
    return qr


async def get_qr_by_short_code(session: AsyncSession, short_code: str) -> Optional[DynamicQR]:
    result = await session.execute(select(DynamicQR).where(DynamicQR.short_code == short_code))
    return result.scalar_one_or_none()


async def list_user_qrs(session: AsyncSession, user_id: int) -> List[DynamicQR]:
    result = await session.execute(select(DynamicQR).where(DynamicQR.user_id == user_id))
    return list(result.scalars().all())


async def update_qr_destination(session: AsyncSession, qr_id: int, destination_url: str) -> Optional[DynamicQR]:
    result = await session.execute(select(DynamicQR).where(DynamicQR.id == qr_id))
    qr = result.scalar_one_or_none()
    if not qr:
        return None
    qr.destination_url = destination_url
    await session.commit()
    await session.refresh(qr)
    return qr


async def record_scan(
    session: AsyncSession,
    qr_id: int,
    ip: Optional[str],
    country: Optional[str],
    region: Optional[str],
    city: Optional[str],
    user_agent: Optional[str],
    device: Optional[str],
    os: Optional[str],
    browser: Optional[str],
    referrer: Optional[str],
) -> QRScan:
    scan = QRScan(
        qr_id=qr_id,
        ip=ip,
        country=country,
        region=region,
        city=city,
        user_agent=user_agent,
        device=device,
        os=os,
        browser=browser,
        referrer=referrer,
    )
    session.add(scan)
    await session.commit()
    await session.refresh(scan)
    return scan


async def list_qr_scans(session: AsyncSession, qr_id: int) -> List[QRScan]:
    result = await session.execute(select(QRScan).where(QRScan.qr_id == qr_id))
    return list(result.scalars().all())



from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from app.models import Subscription


async def create_subscription(
    session: AsyncSession,
    *,
    user_id: int,
    lemon_id: Optional[str],
    status: str,
    plan: str,
    renews_at: Optional[datetime] = None,
    ends_at: Optional[datetime] = None,
) -> Subscription:
    subscription = Subscription(
        user_id=user_id,
        lemon_id=lemon_id,
        status=status,
        plan=plan,
        renews_at=renews_at,
        ends_at=ends_at,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def get_subscription_by_lemon_id(session: AsyncSession, lemon_id: str) -> Optional[Subscription]:
    result = await session.execute(select(Subscription).where(Subscription.lemon_id == lemon_id))
    return result.scalar_one_or_none()


async def get_latest_subscription_for_user(session: AsyncSession, user_id: int) -> Optional[Subscription]:
    result = await session.execute(
        select(Subscription).where(Subscription.user_id == user_id).order_by(desc(Subscription.created_at))
    )
    return result.scalars().first()


async def update_subscription(
    session: AsyncSession,
    subscription_id: int,
    *,
    status: Optional[str] = None,
    plan: Optional[str] = None,
    renews_at: Optional[datetime] = None,
    ends_at: Optional[datetime] = None,
    lemon_id: Optional[str] = None,
) -> Optional[Subscription]:
    result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        return None
    if status is not None:
        subscription.status = status
    if plan is not None:
        subscription.plan = plan
    if renews_at is not None or renews_at is None:
        subscription.renews_at = renews_at
    if ends_at is not None or ends_at is None:
        subscription.ends_at = ends_at
    if lemon_id is not None:
        subscription.lemon_id = lemon_id
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def set_user_free_plan(session: AsyncSession, user_id: int) -> Subscription:
    return await create_subscription(
        session,
        user_id=user_id,
        lemon_id=None,
        status="active",
        plan="free",
        renews_at=None,
        ends_at=None,
    )



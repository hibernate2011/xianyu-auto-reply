"""商品监控的用户级 OpenRouter 凭据，仅供专用接口与调度服务使用。"""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, String, Table, delete, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.base_class import Base


MONITOR_OPENROUTER_KEY_MAX_LENGTH = 512
monitor_openrouter_keys = Table(
    "xy_monitor_openrouter_keys",
    Base.metadata,
    Column("owner_id", BigInteger, ForeignKey("xy_users.id", ondelete="CASCADE"), primary_key=True),
    Column("api_key", String(MONITOR_OPENROUTER_KEY_MAX_LENGTH), nullable=False),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
)


async def get_monitor_openrouter_key(session: AsyncSession, owner_id: int) -> str | None:
    return await session.scalar(
        select(monitor_openrouter_keys.c.api_key).where(monitor_openrouter_keys.c.owner_id == owner_id)
    )


async def set_monitor_openrouter_key(session: AsyncSession, owner_id: int, api_key: str | None) -> None:
    if api_key is None:
        await session.execute(delete(monitor_openrouter_keys).where(monitor_openrouter_keys.c.owner_id == owner_id))
    else:
        statement = insert(monitor_openrouter_keys).values(owner_id=owner_id, api_key=api_key)
        await session.execute(statement.on_duplicate_key_update(api_key=statement.inserted.api_key))
    await session.commit()

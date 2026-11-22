from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import ClassVar

from arq import cron, run_worker
from arq.connections import RedisSettings
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import delete, select, text
from sqlalchemy.exc import SQLAlchemyError

from bot.core.config import settings
from bot.core.db import Database
from bot.models import (
    AutoModMessageEvent,
    LogPrivacySetting,
    LogRecord,
    TempRole,
)


async def startup(ctx):
    ctx["database"] = Database(settings)
    try:
        await ctx["database"].health()
        ctx["database_healthy"] = True
    except (SQLAlchemyError, ConnectionError, TimeoutError, OSError):
        ctx["database_healthy"] = False
    try:
        ctx["redis"] = Redis.from_url(settings.redis_url)
        ctx["redis_healthy"] = bool(await ctx["redis"].ping())
    except RedisError:
        ctx["redis_healthy"] = False


async def shutdown(ctx):
    database = ctx.get("database")
    if database is not None:
        await database.close()
    redis = ctx.get("redis")
    if redis is not None:
        await redis.aclose()


async def ping(ctx):
    return "pong"


async def cleanup_server_logs(ctx):
    database = ctx["database"]
    removed = 0
    async with database.session() as session:
        rows = (
            await session.execute(
                select(LogPrivacySetting)
            )
        ).scalars().all()
        policies = {
            row.guild_id: max(1, min(365, int(row.retention_days)))
            for row in rows
        }
        guild_ids = (
            await session.execute(select(LogRecord.guild_id).distinct())
        ).scalars().all()
        for guild_id in guild_ids:
            cutoff = datetime.now(UTC) - timedelta(
                days=policies.get(guild_id, 30)
            )
            result = await session.execute(
                delete(LogRecord).where(
                    LogRecord.guild_id == guild_id,
                    LogRecord.recorded_at < cutoff,
                )
            )
            removed += result.rowcount or 0
        await session.commit()
    return removed


async def cleanup_automod_message_events(ctx):
    cutoff = datetime.now(UTC) - timedelta(days=1)
    database = ctx["database"]
    async with database.session() as session:
        result = await session.execute(
            delete(AutoModMessageEvent).where(
                AutoModMessageEvent.occurred_at < cutoff
            )
        )
        await session.commit()
        return result.rowcount or 0


async def cleanup_temp_roles(ctx):
    now = datetime.now(UTC)
    database = ctx["database"]
    async with database.session() as session:
        result = await session.execute(
            delete(TempRole).where(TempRole.expires_at <= now)
        )
        await session.commit()
        return result.rowcount or 0


async def database_maintenance(ctx):
    database = ctx["database"]
    async with database.session() as session:
        await session.execute(text("SELECT 1"))
    return True


class WorkerSettings:
    functions: ClassVar[list] = [
        ping,
        cleanup_server_logs,
        cleanup_automod_message_events,
        cleanup_temp_roles,
        database_maintenance,
    ]
    cron_jobs: ClassVar[list] = [
        cron(cleanup_server_logs, hour=3, minute=0),
        cron(cleanup_automod_message_events, hour=3, minute=15),
        cron(cleanup_temp_roles, hour=4, minute=0),
    ]
    on_startup = startup
    on_shutdown = shutdown

    @staticmethod
    def redis_settings():
        return RedisSettings.from_dsn(settings.redis_url)


def main():
    run_worker(WorkerSettings)

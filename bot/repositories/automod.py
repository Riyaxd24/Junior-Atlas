import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import AutoModLog, AutoModMessageEvent, AutoModRule


def merge_rule_config(
    existing,
    *,
    threshold,
    action,
    duration_seconds,
    exempt_roles=None,
    exempt_channels=None,
    custom_data=None,
) -> dict:
    """Merge a rule update with its stored configuration.

    ``exempt_roles``/``exempt_channels`` are optional on purpose: commands that
    only change a threshold or an action must not silently clear an
    administrator's existing exemptions.  Passing an explicit list (including
    an empty list) still replaces the stored value.
    """
    config = dict(existing or {})
    config.update(custom_data or {})
    config["threshold"] = threshold
    if exempt_roles is not None:
        config["exempt_roles"] = sorted({int(value) for value in exempt_roles})
    else:
        config.setdefault("exempt_roles", [])
    if exempt_channels is not None:
        config["exempt_channels"] = sorted({int(value) for value in exempt_channels})
    else:
        config.setdefault("exempt_channels", [])
    config["duration_seconds"] = duration_seconds if action == "timeout" else None
    return config


class AutoModRepository:
    def __init__(self, db):
        self.db = db

    async def get_rules(self, guild_id):
        async with self.db.session() as session:
            rows = (
                await session.execute(
                    select(AutoModRule).where(AutoModRule.guild_id == guild_id)
                )
            ).scalars().all()
            return list(rows)

    async def configure_rule(
        self,
        guild_id,
        rule_type,
        *,
        enabled,
        threshold,
        action,
        duration_seconds,
        exempt_roles=None,
        exempt_channels=None,
        custom_data=None,
    ):
        async with self.db.session() as session:
            existing = await session.scalar(
                select(AutoModRule).where(
                    AutoModRule.guild_id == guild_id,
                    AutoModRule.name == rule_type,
                )
            )
            config = merge_rule_config(
                dict(existing.config or {}) if existing is not None else {},
                threshold=threshold,
                action=action,
                duration_seconds=duration_seconds,
                exempt_roles=exempt_roles,
                exempt_channels=exempt_channels,
                custom_data=custom_data,
            )
            statement = pg_insert(AutoModRule).values(
                guild_id=guild_id,
                name=rule_type,
                kind="filter",
                pattern="",
                action=action,
                enabled=enabled,
                config=config,
            )
            statement = statement.on_conflict_do_update(
                index_elements=[AutoModRule.guild_id, AutoModRule.name],
                set_={
                    "action": statement.excluded.action,
                    "enabled": statement.excluded.enabled,
                    "config": statement.excluded.config,
                },
            )
            await session.execute(statement)
            await session.commit()

    async def record_message_and_count(
        self,
        guild_id,
        user_id,
        channel_id,
        rule_type,
        content,
        window_seconds,
    ):
        content_hash = hashlib.sha256(content.casefold().encode()).hexdigest()
        cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
        async with self.db.session() as session:
            await session.execute(
                delete(AutoModMessageEvent).where(
                    AutoModMessageEvent.guild_id == guild_id,
                    AutoModMessageEvent.occurred_at < cutoff,
                )
            )
            session.add(
                AutoModMessageEvent(
                    guild_id=guild_id,
                    user_id=user_id,
                    channel_id=channel_id,
                    rule_type=rule_type,
                    content_hash=content_hash,
                )
            )
            await session.flush()
            count = await session.scalar(
                select(func.count(AutoModMessageEvent.id)).where(
                    AutoModMessageEvent.guild_id == guild_id,
                    AutoModMessageEvent.user_id == user_id,
                    AutoModMessageEvent.rule_type == rule_type,
                    AutoModMessageEvent.occurred_at >= cutoff,
                )
            )
            await session.commit()
            return int(count or 0)

    async def count_recent_violations(
        self,
        guild_id,
        user_id,
        rule_type,
        window_seconds,
    ):
        cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
        async with self.db.session() as session:
            count = await session.scalar(
                select(func.count(AutoModLog.id)).where(
                    AutoModLog.guild_id == guild_id,
                    AutoModLog.user_id == user_id,
                    AutoModLog.rule_type == rule_type,
                    AutoModLog.created_at >= cutoff,
                )
            )
            return int(count or 0)

    async def add_log(self, log):
        async with self.db.session() as session:
            session.add(log)
            await session.commit()

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import LogPrivacySetting, LogRecord, LogSetting


class LoggingRepository:
    def __init__(self, db):
        self.db = db

    async def set_channel(self, guild_id, event_type, channel_id):
        statement = pg_insert(LogSetting).values(
            guild_id=guild_id,
            event_type=event_type,
            channel_id=channel_id,
            enabled=True,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[LogSetting.guild_id, LogSetting.event_type],
            set_={"channel_id": statement.excluded.channel_id},
        )
        async with self.db.session() as session:
            await session.execute(statement)
            await session.commit()

    async def set_enabled(self, guild_id, event_type, enabled):
        async with self.db.session() as session:
            row = await session.scalar(
                select(LogSetting).where(
                    LogSetting.guild_id == guild_id,
                    LogSetting.event_type == event_type,
                )
            )
            if row is None:
                return False
            row.enabled = enabled
            await session.commit()
            return True

    async def get_configuration(self, guild_id):
        async with self.db.session() as session:
            settings = (
                await session.execute(
                    select(LogSetting).where(LogSetting.guild_id == guild_id)
                )
            ).scalars().all()
            privacy = await session.scalar(
                select(LogPrivacySetting).where(
                    LogPrivacySetting.guild_id == guild_id
                )
            )
            return list(settings), privacy

    async def update_privacy(
        self,
        guild_id,
        include_message_content=None,
        retention_days=None,
        exempt_channel_ids=None,
    ):
        async with self.db.session() as session:
            row = await session.scalar(
                select(LogPrivacySetting).where(
                    LogPrivacySetting.guild_id == guild_id
                )
            )
            if row is None:
                row = LogPrivacySetting(
                    guild_id=guild_id,
                    include_message_content=False,
                    retention_days=30,
                    exempt_channel_ids=[],
                )
                session.add(row)
                await session.flush()
            if include_message_content is not None:
                row.include_message_content = include_message_content
            if retention_days is not None:
                row.retention_days = retention_days
            if exempt_channel_ids is not None:
                row.exempt_channel_ids = exempt_channel_ids
            await session.commit()

    async def add_record(self, record):
        async with self.db.session() as session:
            session.add(record)
            await session.commit()

    async def delete_expired_records(self, guild_id, retention_days):
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        async with self.db.session() as session:
            result = await session.execute(
                delete(LogRecord).where(
                    LogRecord.guild_id == guild_id,
                    LogRecord.recorded_at < cutoff,
                )
            )
            await session.commit()
            return result.rowcount

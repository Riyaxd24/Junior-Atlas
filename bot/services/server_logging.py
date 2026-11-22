from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import discord
from redis.exceptions import RedisError

from bot.models import LogRecord
from bot.repositories.logging import LoggingRepository
from bot.ui.embeds import COLOURS

LOG_EVENT_TYPES = (
    "message_delete",
    "message_edit",
    "member_join",
    "member_leave",
    "member_update",
    "role_change",
    "channel_create",
    "channel_delete",
    "channel_update",
    "voice_state",
    "ban",
    "unban",
    "moderation",
    "invite",
)
MAX_RETENTION_DAYS = 365
MAX_CONTENT_LENGTH = 1000
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LogDelivery:
    channel_id: int
    embed: discord.Embed


class ServerLoggingService:
    def __init__(self, db, cache=None):
        self.repository = LoggingRepository(db)
        self.cache = cache

    async def set_channel(self, guild_id, event_type, channel_id):
        self._validate_event_type(event_type)
        await self.repository.set_channel(guild_id, event_type, channel_id)
        await self.invalidate(guild_id)

    async def set_event_enabled(self, guild_id, event_type, enabled):
        self._validate_event_type(event_type)
        changed = await self.repository.set_enabled(guild_id, event_type, enabled)
        if changed:
            await self.invalidate(guild_id)
        return changed

    async def configure_privacy(
        self,
        guild_id,
        include_message_content=None,
        retention_days=None,
        exempt_channel_ids=None,
    ):
        if retention_days is not None and not 1 <= retention_days <= MAX_RETENTION_DAYS:
            raise ValueError(f"Retention must be between 1 and {MAX_RETENTION_DAYS} days.")
        await self.repository.update_privacy(
            guild_id,
            include_message_content=include_message_content,
            retention_days=retention_days,
            exempt_channel_ids=exempt_channel_ids,
        )
        await self.invalidate(guild_id)

    async def set_channel_exempt(self, guild_id, channel_id, exempt):
        config = await self.get_configuration(guild_id)
        exempt_channels = set(config["exempt_channel_ids"])
        if exempt:
            exempt_channels.add(channel_id)
        else:
            exempt_channels.discard(channel_id)
        await self.configure_privacy(
            guild_id,
            exempt_channel_ids=sorted(exempt_channels),
        )

    async def prepare_event(
        self,
        guild_id,
        event_type,
        title,
        summary,
        channel_id=None,
        actor_id=None,
        target_id=None,
        message_content=None,
        bot_authored=False,
        occurred_at=None,
    ):
        self._validate_event_type(event_type)
        config = await self.get_configuration(guild_id)
        setting = config["events"].get(event_type)
        if setting is None or not setting["enabled"]:
            return None
        if channel_id is not None and channel_id in config["exempt_channel_ids"]:
            return None

        include_content = (
            config["include_message_content"]
            and message_content is not None
            and not bot_authored
        )
        retained_content = message_content[:MAX_CONTENT_LENGTH] if include_content else None
        timestamp = occurred_at or datetime.now(UTC)

        await self.repository.add_record(
            LogRecord(
                guild_id=guild_id,
                event_type=event_type,
                channel_id=channel_id,
                actor_id=actor_id,
                target_id=target_id,
                summary=summary[:500],
                content=retained_content,
                recorded_at=timestamp,
            )
        )
        await self.repository.delete_expired_records(
            guild_id,
            config["retention_days"],
        )
        embed = build_log_embed(
            title=title,
            summary=summary,
            guild_id=guild_id,
            channel_id=channel_id,
            actor_id=actor_id,
            target_id=target_id,
            content=retained_content,
            timestamp=timestamp,
        )
        return LogDelivery(setting["channel_id"], embed)

    async def get_configuration(self, guild_id):
        key = f"server-logs:{guild_id}"
        if self.cache is not None:
            try:
                cached = await self.cache.get_json(key)
                if cached is not None:
                    return cached
            except RedisError:
                log.warning("server log Redis cache read unavailable guild=%s", guild_id)
        settings, privacy = await self.repository.get_configuration(guild_id)
        config = {
            "events": {
                setting.event_type: {
                    "channel_id": setting.channel_id,
                    "enabled": setting.enabled,
                }
                for setting in settings
            },
            "include_message_content": (
                privacy.include_message_content if privacy else False
            ),
            "retention_days": privacy.retention_days if privacy else 30,
            "exempt_channel_ids": privacy.exempt_channel_ids if privacy else [],
        }
        if self.cache is not None:
            try:
                await self.cache.set_json(key, config, ttl=300)
            except RedisError:
                log.warning("server log Redis cache write unavailable guild=%s", guild_id)
        return config

    async def invalidate(self, guild_id):
        if self.cache is not None:
            try:
                await self.cache.delete(f"server-logs:{guild_id}")
            except RedisError:
                log.warning("server log Redis invalidation unavailable guild=%s", guild_id)

    @staticmethod
    def _validate_event_type(event_type):
        if event_type not in LOG_EVENT_TYPES:
            raise ValueError("Unsupported log event type.")


def build_log_embed(
    *,
    title,
    summary,
    guild_id,
    channel_id=None,
    actor_id=None,
    target_id=None,
    content=None,
    timestamp=None,
):
    embed = discord.Embed(
        title=title,
        description=summary[:4000],
        colour=COLOURS["info"],
        timestamp=timestamp or datetime.now(UTC),
    )
    embed.set_footer(text="Junior Atlas")
    embed.add_field(name="Guild ID", value=str(guild_id), inline=True)
    if channel_id is not None:
        embed.add_field(name="Channel ID", value=str(channel_id), inline=True)
    if actor_id is not None:
        embed.add_field(name="Actor ID", value=str(actor_id), inline=True)
    if target_id is not None:
        embed.add_field(name="Target ID", value=str(target_id), inline=True)
    if content:
        embed.add_field(name="Message content", value=content[:1024], inline=False)
    return embed

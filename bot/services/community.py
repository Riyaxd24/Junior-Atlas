import logging
import random

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import CollectibleItem, TempVoiceChannel, TempVoiceSetting, UserCollection

log = logging.getLogger(__name__)


class CommunityService:
    def __init__(self, db, cache=None):
        self.db = db
        self.cache = cache

    async def daily_collect(self, guild_id, user_id):
        key = f"collection:{guild_id}:{user_id}"
        if self.cache is not None:
            try:
                allowed = await self.cache.client.set(key, "1", nx=True, ex=86400)
                if not allowed:
                    return None
            except RedisError:
                log.warning("daily collectible Redis cooldown unavailable guild=%s", guild_id)
        async with self.db.session() as session:
            items = (
                await session.execute(
                    select(CollectibleItem).where(
                        CollectibleItem.guild_id == guild_id
                    )
                )
            ).scalars().all()
            if not items:
                item = CollectibleItem(
                    guild_id=guild_id,
                    name="First Star",
                    category="badge",
                    rarity="common",
                    description="A first-star daily collectible.",
                    emoji="✨",
                )
                session.add(item)
                await session.flush()
                items = [item]
            item = random.choice(items)
            await session.execute(
                pg_insert(UserCollection)
                .values(guild_id=guild_id, user_id=user_id, item_id=item.id, count=1)
                .on_conflict_do_update(
                    index_elements=[
                        UserCollection.guild_id,
                        UserCollection.user_id,
                        UserCollection.item_id,
                    ],
                    set_={"count": UserCollection.count + 1},
                )
            )
            await session.commit()
            return item

    async def configure_temp_voice(
        self,
        guild_id,
        hub_channel_id,
        category_id,
        default_name,
        user_limit,
    ):
        async with self.db.session() as session:
            setting = await session.scalar(
                select(TempVoiceSetting).where(
                    TempVoiceSetting.guild_id == guild_id,
                    TempVoiceSetting.hub_channel_id == hub_channel_id,
                )
            )
            if setting is None:
                setting = TempVoiceSetting(
                    guild_id=guild_id,
                    hub_channel_id=hub_channel_id,
                    category_id=category_id,
                    default_name=default_name,
                    user_limit=user_limit,
                )
                session.add(setting)
            else:
                setting.category_id = category_id
                setting.default_name = default_name
                setting.user_limit = user_limit
            await session.commit()

    async def create_temp_voice(self, guild, member, hub_channel_id):
        async with self.db.session() as session:
            setting = await session.scalar(
                select(TempVoiceSetting).where(
                    TempVoiceSetting.guild_id == guild.id,
                    TempVoiceSetting.hub_channel_id == hub_channel_id,
                )
            )
        if setting is None:
            return None
        category = guild.get_channel(setting.category_id) if setting.category_id else hub_channel_id
        channel = await guild.create_voice_channel(
            name=setting.default_name.format(user=member.display_name),
            category=category if hasattr(category, "type") else None,
            user_limit=setting.user_limit,
            reason="Junior Atlas temporary voice channel",
        )
        await member.move_to(channel)
        async with self.db.session() as session:
            session.add(
                TempVoiceChannel(
                    guild_id=guild.id,
                    channel_id=channel.id,
                    owner_id=member.id,
                )
            )
            await session.commit()
        return channel

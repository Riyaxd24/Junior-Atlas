from sqlalchemy import BigInteger, Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .schema import Base


class CollectibleItem(Base):
    __tablename__ = "collectible_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False, default="common")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    emoji: Mapped[str] = mapped_column(String(50), nullable=False, default="✨")
    __table_args__ = (
        UniqueConstraint("guild_id", "name"),
    )


class UserCollection(Base):
    __tablename__ = "user_collections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __table_args__ = (
        UniqueConstraint("guild_id", "user_id", "item_id"),
    )


class GiveawayEntry(Base):
    __tablename__ = "giveaway_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    giveaway_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint("giveaway_id", "user_id"),
    )


class TempVoiceSetting(Base):
    __tablename__ = "temp_voice_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    hub_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    category_id: Mapped[int | None] = mapped_column(BigInteger)
    default_name: Mapped[str] = mapped_column(String(100), nullable=False, default="{user}'s Channel")
    user_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TempVoiceChannel(Base):
    __tablename__ = "temp_voice_channels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Poll(Base):
    __tablename__ = "polls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    options_json: Mapped[str] = mapped_column(Text, nullable=False)
    votes_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class StarboardMessage(Base):
    __tablename__ = "starboard_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    original_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    starboard_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    stars_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

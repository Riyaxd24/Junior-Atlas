from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .schema import Base


class LogSetting(Base):
    __tablename__ = "log_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (
        UniqueConstraint("guild_id", "event_type"),
    )


class LogPrivacySetting(Base):
    __tablename__ = "log_privacy_settings"
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    include_message_content: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    exempt_channel_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )


class LogRecord(Base):
    __tablename__ = "log_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger)
    actor_id: Mapped[int | None] = mapped_column(BigInteger)
    target_id: Mapped[int | None] = mapped_column(BigInteger)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    __table_args__ = (
        Index("ix_log_records_guild_recorded_at", "guild_id", "recorded_at"),
    )

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .schema import Base


class VerificationSetting(Base):
    __tablename__ = "verification_settings"
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger)
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    verified_role_id: Mapped[int | None] = mapped_column(BigInteger)
    rules_text: Mapped[str | None] = mapped_column(Text)
    log_channel_id: Mapped[int | None] = mapped_column(BigInteger)
    extra_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class RoleMenu(Base):
    __tablename__ = "role_menus"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    menu_type: Mapped[str] = mapped_column(String(32), nullable=False, default="select")
    max_values: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_exclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RoleMenuItem(Base):
    __tablename__ = "role_menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(200))


class TempRole(Base):
    __tablename__ = "temp_roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    __table_args__ = (
        Index(
            "ix_temp_roles_guild_user_role",
            "guild_id",
            "user_id",
            "role_id",
            unique=True,
        ),
    )

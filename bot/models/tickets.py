from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .schema import Base


class TicketPanel(Base):
    __tablename__ = "ticket_panels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    category_id: Mapped[int | None] = mapped_column(BigInteger)
    support_role_id: Mapped[int | None] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(100), nullable=False, default="Support Tickets")
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Click below to open a ticket.",
    )


class TicketRecord(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    ticket_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    claimed_by_id: Mapped[int | None] = mapped_column(BigInteger)
    closed_by_id: Mapped[int | None] = mapped_column(BigInteger)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_reason: Mapped[str | None] = mapped_column(Text)
    panel_id: Mapped[int | None] = mapped_column(Integer)
    __table_args__ = (
        Index("ix_tickets_guild_status", "guild_id", "status"),
        Index("ix_tickets_guild_number", "guild_id", "ticket_number", unique=True),
    )


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments_json: Mapped[str | None] = mapped_column(Text)

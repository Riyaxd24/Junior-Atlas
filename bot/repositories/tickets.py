from datetime import UTC, datetime

from sqlalchemy import func, select

from bot.models import TicketMessage, TicketPanel, TicketRecord


class TicketRepository:
    def __init__(self, db):
        self.db = db

    async def create_panel(
        self,
        guild_id,
        channel_id,
        message_id,
        category_id,
        support_role_id,
        title,
        description,
    ):
        async with self.db.session() as session:
            panel = TicketPanel(
                guild_id=guild_id,
                channel_id=channel_id,
                message_id=message_id,
                category_id=category_id,
                support_role_id=support_role_id,
                title=title,
                description=description,
            )
            session.add(panel)
            await session.commit()
            await session.refresh(panel)
            return panel

    async def get_panel_by_message(self, message_id):
        async with self.db.session() as session:
            return await session.scalar(
                select(TicketPanel).where(TicketPanel.message_id == message_id)
            )

    async def create_ticket(self, guild_id, channel_id, creator_id, panel_id=None):
        async with self.db.session() as session:
            number = await session.scalar(
                select(func.coalesce(func.max(TicketRecord.ticket_number), 0)).where(
                    TicketRecord.guild_id == guild_id
                )
            )
            ticket = TicketRecord(
                guild_id=guild_id,
                channel_id=channel_id,
                creator_id=creator_id,
                ticket_number=int(number or 0) + 1,
                status="open",
                panel_id=panel_id,
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket

    async def get_ticket_by_channel(self, channel_id):
        async with self.db.session() as session:
            return await session.scalar(
                select(TicketRecord).where(TicketRecord.channel_id == channel_id)
            )

    async def transition(self, channel_id, *, status, user_id=None, reason=None):
        async with self.db.session() as session:
            ticket = await session.scalar(
                select(TicketRecord).where(TicketRecord.channel_id == channel_id)
            )
            if ticket is None:
                return None
            if status == "claimed":
                if ticket.status != "open":
                    return None
                ticket.status = "claimed"
                ticket.claimed_by_id = user_id
            elif status == "unclaimed":
                if ticket.status != "claimed":
                    return None
                ticket.status = "open"
                ticket.claimed_by_id = None
            elif status == "closed":
                if ticket.status == "closed":
                    return None
                ticket.status = "closed"
                ticket.closed_by_id = user_id
                ticket.closed_at = datetime.now(UTC)
                ticket.close_reason = reason
            elif status == "open":
                if ticket.status != "closed":
                    return None
                ticket.status = "open"
                ticket.closed_by_id = None
                ticket.closed_at = None
                ticket.close_reason = None
            await session.commit()
            await session.refresh(ticket)
            return ticket

    async def record_transcript(self, ticket_id, messages):
        async with self.db.session() as session:
            ticket = await session.scalar(
                select(TicketRecord).where(TicketRecord.id == ticket_id)
            )
            if ticket is None:
                return 0
            for message in messages:
                session.add(
                    TicketMessage(
                        ticket_id=ticket.id,
                        author_id=message.author.id,
                        author_tag=str(message.author),
                        content=message.content[:4000],
                        attachments_json=None,
                    )
                )
            await session.commit()
            return len(messages)

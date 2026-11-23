from __future__ import annotations

import discord

TICKET_TOPIC_PREFIX = "junior-atlas-ticket-owner:"
# Tickets created before the rebrand keep working; new tickets use the new prefix.
LEGACY_TICKET_TOPIC_PREFIX = "fallen-ticket-owner:"
TICKET_TOPIC_PREFIXES = (TICKET_TOPIC_PREFIX, LEGACY_TICKET_TOPIC_PREFIX)


def ticket_owner_id(topic: str | None) -> int | None:
    """Extract the ticket opener ID from current or legacy channel topics."""
    raw = topic or ""
    for prefix in TICKET_TOPIC_PREFIXES:
        marker = f"{prefix}"
        if marker in raw:
            try:
                return int(raw.split(marker, 1)[1].split()[0])
            except (ValueError, IndexError):
                return None
    return None


class TicketService:
    async def create(self, guild, category, member):
        if guild is None or member is None:
            raise ValueError("ticket creation requires a guild and member")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
        }
        staff_roles = [
            role for role in guild.roles
            if not role.is_default() and role.permissions.manage_channels
        ]
        for role in staff_roles:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
        me = guild.me
        if me:
            overwrites[me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )

        base = f"ticket-{member.id}"
        expected_topics = {f"{prefix}{member.id}" for prefix in TICKET_TOPIC_PREFIXES}
        existing = discord.utils.find(
            lambda ch: getattr(ch, "topic", "") in expected_topics,
            guild.text_channels,
        )
        if existing:
            return existing

        return await guild.create_text_channel(
            base[:90],
            category=category,
            overwrites=overwrites,
            topic=f"{TICKET_TOPIC_PREFIX}{member.id}",
            reason="Ticket created",
        )

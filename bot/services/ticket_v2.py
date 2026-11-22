from __future__ import annotations

import discord

from bot.repositories.tickets import TicketRepository


class TicketService:
    def __init__(self, db):
        self.repository = TicketRepository(db)

    async def create_panel(
        self,
        guild,
        channel,
        category,
        support_role,
        title,
        description,
    ):
        embed = discord.Embed(
            title=title[:100],
            description=description[:4000],
            colour=discord.Colour(0x5865F2),
        )
        embed.set_footer(text="Junior Atlas")
        view = TicketPanelView()
        message = await channel.send(embed=embed, view=view)
        panel = await self.repository.create_panel(
            guild.id,
            channel.id,
            message.id,
            category.id if category is not None else None,
            support_role.id if support_role is not None else None,
            title[:100],
            description[:4000],
        )
        view.panel_id = panel.message_id
        return panel, message

    async def open_ticket(self, guild, member, panel_id=None):
        category_id = None
        support_role_id = None
        if panel_id is not None:
            panel = await self.repository.get_panel_by_message(panel_id)
            if panel is not None:
                category_id = panel.category_id
                support_role_id = panel.support_role_id
        category = guild.get_channel(category_id) if category_id else None
        support_role = guild.get_role(support_role_id) if support_role_id else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }
        if support_role is not None:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
            )
        existing = await self.repository.get_ticket_by_channel(
            0
        )
        if existing is not None:
            return None
        channel = await guild.create_text_channel(
            name=f"ticket-{member.id}",
            category=category if isinstance(category, discord.CategoryChannel) else None,
            overwrites=overwrites,
            topic=f"junior-atlas-ticket-owner:{member.id}",
            reason=f"Ticket opened by {member}",
        )
        ticket = await self.repository.create_ticket(
            guild.id,
            channel.id,
            member.id,
            panel_id,
        )
        embed = discord.Embed(
            title=f"Support Ticket #{ticket.ticket_number}",
            description=f"Welcome {member.mention}. Staff will assist you here.",
            colour=discord.Colour(0x5865F2),
        )
        await channel.send(embed=embed, view=TicketControlView())
        return channel

    async def claim(self, channel_id, staff_id):
        return await self.repository.transition(
            channel_id,
            status="claimed",
            user_id=staff_id,
        )

    async def close(self, channel_id, user_id, reason):
        return await self.repository.transition(
            channel_id,
            status="closed",
            user_id=user_id,
            reason=reason,
        )

    async def reopen(self, channel_id):
        return await self.repository.transition(
            channel_id,
            status="open",
        )

    async def transcript(self, ticket, channel):
        messages = [
            message
            async for message in channel.history(limit=500, oldest_first=True)
        ]
        return await self.repository.record_transcript(ticket.id, messages)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.panel_id = None

    @discord.ui.button(
        label="Open Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="junior-atlas:ticket-open",
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This button only works in a server.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        service = TicketService(interaction.client.db)
        channel = await service.open_ticket(
            interaction.guild,
            interaction.user,
            panel_id=self.panel_id,
        )
        if channel is None:
            await interaction.followup.send(
                "A ticket could not be opened.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            f"Ticket opened: {channel.mention}",
            ephemeral=True,
        )


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim",
        style=discord.ButtonStyle.primary,
        custom_id="junior-atlas:ticket-claim",
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return
        service = TicketService(interaction.client.db)
        ticket = await service.claim(interaction.channel_id, interaction.user.id)
        if ticket is None:
            await interaction.response.send_message(
                "This ticket cannot be claimed.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Ticket claimed by {interaction.user.mention}.",
        )

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        custom_id="junior-atlas:ticket-close",
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return
        service = TicketService(interaction.client.db)
        ticket = await service.close(
            interaction.channel_id,
            interaction.user.id,
            "Closed by staff or creator",
        )
        if ticket is None:
            await interaction.response.send_message(
                "This ticket cannot be closed.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Ticket closed. Reopen from the ticket panel or channel controls.",
        )

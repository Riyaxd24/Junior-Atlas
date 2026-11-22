from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.services.ticket_v2 import TicketControlView, TicketPanelView, TicketService
from bot.ui import success_embed


class Tickets(commands.Cog):
    def __init__(self,bot): self.bot=bot
    @app_commands.command(name='ticket',description='Create a private support ticket')
    @app_commands.guild_only()
    async def ticket(self,i):
        await i.response.defer(ephemeral=True)
        ch=await self.bot.tickets.create(i.guild,None,i.user)
        await self.bot.extreme.ticket_create(i.guild_id,ch.id,i.user.id)
        await ch.send(f'🎫 Welcome {i.user.mention}. Staff can help you here.')
        await i.followup.send(embed=success_embed('Ticket created', f'Your private support channel is {ch.mention}.'),ephemeral=True)

    @app_commands.command(name='ticket-panel',description='Post a persistent ticket panel')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_panel(
        self,
        i,
        channel: discord.TextChannel,
        category: discord.CategoryChannel | None = None,
        support_role: discord.Role | None = None,
        title: str = "Support Tickets",
        description: str = "Click below to open a private support ticket.",
    ):
        await i.response.defer(ephemeral=True)
        service = TicketService(self.bot.db)
        _, _message = await service.create_panel(
            i.guild,
            channel,
            category,
            support_role,
            title,
            description,
        )
        await i.followup.send(
            f"Ticket panel posted in {channel.mention}.",
            ephemeral=True,
        )


async def setup(bot):
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControlView())
    await bot.add_cog(Tickets(bot))

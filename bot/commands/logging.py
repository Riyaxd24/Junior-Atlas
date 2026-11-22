from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.services.server_logging import LOG_EVENT_TYPES, ServerLoggingService

log = logging.getLogger(__name__)
EVENT_CHOICES = [
    app_commands.Choice(name=value.replace("_", " ").title(), value=value)
    for value in LOG_EVENT_TYPES
]


class ServerLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = ServerLoggingService(bot.db, bot.cache)
        self._warned_delivery: set[tuple[int, int]] = set()

    logs = app_commands.Group(
        name="logs",
        description="Configure server event logging",
    )

    @logs.command(name="channel", description="Set a log event channel")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(event=EVENT_CHOICES)
    async def set_channel(
        self,
        interaction: discord.Interaction,
        event: app_commands.Choice[str],
        channel: discord.TextChannel,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        await self.service.set_channel(
            interaction.guild.id,
            event.value,
            channel.id,
        )
        await interaction.response.send_message(
            f"{event.name} logs will be sent to {channel.mention}.",
            ephemeral=True,
        )

    @logs.command(name="toggle", description="Enable or disable an event")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(event=EVENT_CHOICES)
    async def toggle(
        self,
        interaction: discord.Interaction,
        event: app_commands.Choice[str],
        enabled: bool,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        changed = await self.service.set_event_enabled(
            interaction.guild.id,
            event.value,
            enabled,
        )
        if not changed:
            await interaction.response.send_message(
                f"Set a channel for {event.name} before enabling it.",
                ephemeral=True,
            )
            return
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(
            f"{event.name} logging is {state}.",
            ephemeral=True,
        )

    @logs.command(name="privacy", description="Configure message and retention privacy")
    @app_commands.default_permissions(administrator=True)
    async def privacy(
        self,
        interaction: discord.Interaction,
        include_message_content: bool,
        retention_days: app_commands.Range[int, 1, 365],
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        await self.service.configure_privacy(
            interaction.guild.id,
            include_message_content=include_message_content,
            retention_days=retention_days,
        )
        await interaction.response.send_message(
            "Log privacy and retention updated.",
            ephemeral=True,
        )

    @logs.command(name="exempt", description="Include or exclude a channel")
    @app_commands.default_permissions(administrator=True)
    async def exempt(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        exempt: bool,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        await self.service.set_channel_exempt(
            interaction.guild.id,
            channel.id,
            exempt,
        )
        await interaction.response.send_message(
            f"{channel.mention} logging exemption updated.",
            ephemeral=True,
        )

    async def _emit(
        self,
        guild,
        event_type,
        title,
        summary,
        *,
        channel_id=None,
        actor_id=None,
        target_id=None,
        message_content=None,
        bot_authored=False,
        occurred_at=None,
    ):
        try:
            delivery = await self.service.prepare_event(
                guild.id,
                event_type,
                title,
                summary,
                channel_id=channel_id,
                actor_id=actor_id,
                target_id=target_id,
                message_content=message_content,
                bot_authored=bot_authored,
                occurred_at=occurred_at,
            )
        except Exception:
            log.exception("server log event failed guild=%s event=%s", guild.id, event_type)
            return
        if delivery is None:
            return
        channel = guild.get_channel(delivery.channel_id)
        warning_key = (guild.id, delivery.channel_id)
        if channel is None:
            if warning_key not in self._warned_delivery:
                log.warning(
                    "configured server log channel is unavailable guild=%s channel=%s",
                    guild.id,
                    delivery.channel_id,
                )
                self._warned_delivery.add(warning_key)
            return
        permissions = channel.permissions_for(guild.me)
        if not getattr(permissions, "send_messages", False):
            if warning_key not in self._warned_delivery:
                log.warning(
                    "bot cannot send to configured server log channel guild=%s channel=%s",
                    guild.id,
                    delivery.channel_id,
                )
                self._warned_delivery.add(warning_key)
            return
        try:
            await channel.send(embed=delivery.embed)
        except discord.HTTPException:
            log.warning(
                "server log delivery failed guild=%s channel=%s",
                guild.id,
                delivery.channel_id,
            )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return
        await self._emit(
            message.guild,
            "message_delete",
            "Message deleted",
            "A message was deleted.",
            channel_id=message.channel.id,
            target_id=message.author.id,
            message_content=message.content,
            bot_authored=message.author.bot,
            occurred_at=message.created_at,
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.guild is None or before.content == after.content:
            return
        await self._emit(
            after.guild,
            "message_edit",
            "Message edited",
            "A message was edited.",
            channel_id=after.channel.id,
            target_id=after.author.id,
            message_content=f"Before: {before.content[:500]}\nAfter: {after.content[:500]}",
            bot_authored=after.author.bot,
            occurred_at=after.edited_at or after.created_at,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self._emit(
            member.guild,
            "member_join",
            "Member joined",
            f"{member} joined the server.",
            target_id=member.id,
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self._emit(
            member.guild,
            "member_leave",
            "Member left",
            f"{member} left the server.",
            target_id=member.id,
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        changes = []
        if before.display_name != after.display_name:
            changes.append(
                f"Display name: `{before.display_name}` -> `{after.display_name}`"
            )
        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}
        added = after_roles - before_roles
        removed = before_roles - after_roles
        if added:
            changes.append(f"Roles added: {', '.join(str(role_id) for role_id in sorted(added))}")
        if removed:
            changes.append(f"Roles removed: {', '.join(str(role_id) for role_id in sorted(removed))}")
        if not changes:
            return
        await self._emit(
            after.guild,
            "member_update",
            "Member updated",
            "\n".join(changes),
            target_id=after.id,
        )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self._emit(
            role.guild,
            "role_change",
            "Role created",
            f"`{role.name}` was created.",
            target_id=role.id,
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self._emit(
            role.guild,
            "role_change",
            "Role deleted",
            f"`{role.name}` was deleted.",
            target_id=role.id,
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.name == after.name and before.permissions == after.permissions:
            return
        await self._emit(
            after.guild,
            "role_change",
            "Role updated",
            f"`{before.name}` changed to `{after.name}`.",
            target_id=after.id,
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self._emit(
            channel.guild,
            "channel_create",
            "Channel created",
            f"`{channel.name}` was created.",
            channel_id=channel.id,
            target_id=channel.id,
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self._emit(
            channel.guild,
            "channel_delete",
            "Channel deleted",
            f"`{channel.name}` was deleted.",
            channel_id=channel.id,
            target_id=channel.id,
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name == after.name:
            return
        await self._emit(
            after.guild,
            "channel_update",
            "Channel updated",
            f"`{before.name}` changed to `{after.name}`.",
            channel_id=after.id,
            target_id=after.id,
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if after.channel is not None:
            summary = f"{member} joined voice channel `{after.channel.name}`."
        elif before.channel is not None:
            summary = f"{member} left voice channel `{before.channel.name}`."
        else:
            return
        await self._emit(
            member.guild,
            "voice_state",
            "Voice state changed",
            summary,
            target_id=member.id,
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self._emit(
            guild,
            "ban",
            "Member banned",
            f"{user} was banned.",
            target_id=user.id,
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self._emit(
            guild,
            "unban",
            "Member unbanned",
            f"{user} was unbanned.",
            target_id=user.id,
        )


async def setup(bot):
    await bot.add_cog(ServerLogging(bot))

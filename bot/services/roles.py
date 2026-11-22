from __future__ import annotations

from datetime import timedelta

import discord

from bot.repositories.roles import RolesRepository


class RolesService:
    def __init__(self, db):
        self.repository = RolesRepository(db)

    async def configure_verification(
        self,
        guild_id,
        channel_id,
        message_id,
        verified_role_id,
        rules_text,
        log_channel_id=None,
    ):
        return await self.repository.save_verification(
            guild_id,
            enabled=True,
            channel_id=channel_id,
            message_id=message_id,
            verified_role_id=verified_role_id,
            rules_text=rules_text,
            log_channel_id=log_channel_id,
        )

    async def get_verification(self, guild_id):
        return await self.repository.get_verification(guild_id)

    async def create_role_menu(
        self,
        *,
        guild_id,
        channel_id,
        message_id,
        name,
        is_exclusive,
        max_values,
        items,
    ):
        return await self.repository.create_role_menu(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            name=name,
            is_exclusive=is_exclusive,
            max_values=max_values,
            items=items,
        )

    async def get_role_menu(self, message_id):
        return await self.repository.get_role_menu(message_id)

    async def list_role_menus(self):
        return await self.repository.list_role_menus()

    async def assign_temp_role(
        self,
        guild,
        member,
        role,
        duration_minutes,
        *,
        reason,
    ):
        me = guild.me
        if role.is_default() or role.managed or role >= me.top_role:
            raise ValueError("The role is not safely assignable by the bot.")
        if duration_minutes < 1 or duration_minutes > 43200:
            raise ValueError("Temporary role duration must be between 1 minute and 30 days.")
        await member.add_roles(role, reason=reason)
        expires_at = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
        await self.repository.assign_temp_role(
            guild.id,
            member.id,
            role.id,
            expires_at,
        )
        return expires_at

    async def expire_temp_roles(self, guilds, limit=100):
        removed = 0
        for row in await self.repository.due_temp_roles(limit):
            guild = guilds.get(row.guild_id)
            if guild is None:
                continue
            member = guild.get_member(row.user_id)
            role = guild.get_role(row.role_id)
            if member is not None and role is not None:
                try:
                    await member.remove_roles(role, reason="Temporary role expired")
                except discord.HTTPException:
                    continue
            await self.repository.delete_temp_role(row)
            removed += 1
        return removed

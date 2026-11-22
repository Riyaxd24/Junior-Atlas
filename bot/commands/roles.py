from __future__ import annotations

import asyncpg
import discord
from discord.ext import commands
from sqlalchemy.exc import SQLAlchemyError

from bot.services.roles import RolesService


class VerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept & Verify",
        style=discord.ButtonStyle.success,
        custom_id="junior-atlas:verify",
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Verification only works inside a server.",
                ephemeral=True,
            )
            return
        service = RolesService(interaction.client.db)
        setting = await service.get_verification(interaction.guild.id)
        if setting is None or not setting.enabled or setting.verified_role_id is None:
            await interaction.response.send_message(
                "Verification is not configured.",
                ephemeral=True,
            )
            return
        role = interaction.guild.get_role(setting.verified_role_id)
        me = interaction.guild.me
        if role is None or role.is_default() or role.managed:
            await interaction.response.send_message(
                "The verified role is not available.",
                ephemeral=True,
            )
            return
        if me is None or role >= me.top_role:
            await interaction.response.send_message(
                "The bot cannot assign the verified role.",
                ephemeral=True,
            )
            return
        try:
            await interaction.user.add_roles(role, reason="Button verification")
        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord denied the role change.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"You have been verified as {role.mention}.",
            ephemeral=True,
        )


class RoleSelect(discord.ui.Select):
    def __init__(self, *, custom_id, options, max_values):
        super().__init__(
            placeholder="Choose roles",
            min_values=0,
            max_values=max_values,
            options=options,
            custom_id=custom_id,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Role menus only work inside a server.",
                ephemeral=True,
            )
            return
        message_id = int(self.custom_id.rsplit(":", 1)[1])
        service = RolesService(interaction.client.db)
        menu_and_items = await service.get_role_menu(message_id)
        if menu_and_items is None:
            await interaction.response.send_message(
                "This role menu is no longer configured.",
                ephemeral=True,
            )
            return
        menu, items = menu_and_items
        if menu.guild_id != interaction.guild.id:
            await interaction.response.send_message(
                "This role menu belongs to another server.",
                ephemeral=True,
            )
            return
        selected_ids = {int(value) for value in self.values}
        me = interaction.guild.me
        for item in items:
            role = interaction.guild.get_role(item.role_id)
            if role is None or role.is_default() or role.managed:
                continue
            if me is None or role >= me.top_role:
                continue
            if item.role_id in selected_ids:
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Role menu selection")
            elif menu.is_exclusive or role in interaction.user.roles:
                await interaction.user.remove_roles(role, reason="Role menu selection")
        await interaction.response.send_message(
            "Your role selection has been updated.",
            ephemeral=True,
        )


class RoleMenuView(discord.ui.View):
    def __init__(self, *, message_id, options, max_values):
        super().__init__(timeout=None)
        self.add_item(
            RoleSelect(
                custom_id=f"junior-atlas:roles:{message_id}",
                options=options,
                max_values=max_values,
            )
        )


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = RolesService(bot.db)

async def setup(bot):
    bot.add_view(VerificationButton())
    service = RolesService(bot.db)
    try:
        for menu, items in await service.list_role_menus():
            options = [
                discord.SelectOption(
                    label=item.label[:100],
                    value=str(item.role_id),
                    description=(item.description or "")[:100] or None,
                )
                for item in items
            ]
            bot.add_view(
                RoleMenuView(
                    message_id=menu.message_id,
                    options=options,
                    max_values=menu.max_values,
                )
            )
    except (asyncpg.PostgresError, ConnectionError, TimeoutError, OSError, SQLAlchemyError):
        bot.log.exception("could not re-register persisted role menus")
    await bot.add_cog(Roles(bot))

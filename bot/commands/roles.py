from __future__ import annotations

import asyncpg
import discord
from discord import app_commands
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

    verify = app_commands.Group(
        name="verify",
        description="Configure button verification",
    )

    @verify.command(name="setup", description="Post a persistent verification button")
    @app_commands.default_permissions(administrator=True)
    async def setup_verification(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        channel: discord.TextChannel,
        rules: str = "Accept the server rules to gain access.",
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        me = interaction.guild.me
        if role.is_default() or role.managed or me is None or role >= me.top_role:
            await interaction.response.send_message(
                "The verified role must be below my highest role.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Server Verification",
            description=rules[:4000],
            colour=discord.Colour(0x5865F2),
        )
        embed.set_footer(text="Junior Atlas")
        message = await channel.send(embed=embed, view=VerificationButton())
        await self.service.configure_verification(
            interaction.guild.id,
            channel.id,
            message.id,
            role.id,
            rules,
        )
        await interaction.followup.send(
            f"Verification panel posted in {channel.mention}.",
            ephemeral=True,
        )

    roles_menu = app_commands.Group(
        name="roles-menu",
        description="Create persistent role-selection menus",
    )

    @roles_menu.command(name="create", description="Create a role-selection menu")
    @app_commands.default_permissions(manage_roles=True)
    async def create_role_menu(
        self,
        interaction: discord.Interaction,
        name: str,
        role1: discord.Role,
        role2: discord.Role | None = None,
        role3: discord.Role | None = None,
        exclusive: bool = True,
        channel: discord.TextChannel | None = None,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message(
                "Choose a text channel.",
                ephemeral=True,
            )
            return
        roles = [role for role in (role1, role2, role3) if role is not None]
        unique_roles = list(dict.fromkeys(roles))
        me = interaction.guild.me
        for role in unique_roles:
            if role.is_default() or role.managed or me is None or role >= me.top_role:
                await interaction.response.send_message(
                    f"{role.mention} is not safely assignable by the bot.",
                    ephemeral=True,
                )
                return
        options = [
            discord.SelectOption(
                label=role.name[:100],
                value=str(role.id),
                description=f"Toggle {role.name}"[:100],
            )
            for role in unique_roles
        ]
        await interaction.response.defer(ephemeral=True)
        seed_message = await target_channel.send(
            f"Role menu: **{name[:100]}**",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        view = RoleMenuView(
            message_id=seed_message.id,
            options=options,
            max_values=1 if exclusive else len(options),
        )
        await seed_message.edit(
            content=f"Role menu: **{name[:100]}**",
            view=view,
        )
        await self.service.create_role_menu(
            guild_id=interaction.guild.id,
            channel_id=target_channel.id,
            message_id=seed_message.id,
            name=name[:100],
            is_exclusive=exclusive,
            max_values=1 if exclusive else len(options),
            items=[
                (role.id, role.name[:100], None, f"Toggle {role.name}"[:200])
                for role in unique_roles
            ],
        )
        await interaction.followup.send(
            f"Role menu posted in {target_channel.mention}.",
            ephemeral=True,
        )

    temp = app_commands.Group(
        name="temp-role",
        description="Assign temporary roles",
    )

    @temp.command(name="assign", description="Assign a role temporarily")
    @app_commands.default_permissions(manage_roles=True)
    async def assign_temp(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        minutes: app_commands.Range[int, 1, 43200],
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        try:
            expires_at = await self.service.assign_temp_role(
                interaction.guild,
                member,
                role,
                minutes,
                reason=f"Temporary role assigned by {interaction.user}",
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord denied the role change.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"{role.mention} assigned to {member.mention} until "
            f"<t:{int(expires_at.timestamp())}:R>.",
            ephemeral=True,
        )


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

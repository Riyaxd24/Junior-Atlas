from __future__ import annotations

import logging
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from bot.services.automod_v3 import (
    ESCALATION_ACTIONS,
    RULE_ACTIONS,
    RULE_TYPES,
    AutoModService,
)

log = logging.getLogger(__name__)
FILTER_CHOICES = [
    app_commands.Choice(name=value.replace("_", " ").title(), value=value)
    for value in RULE_TYPES
]
ACTION_CHOICES = [
    app_commands.Choice(name=value.title(), value=value)
    for value in RULE_ACTIONS
]
ESCALATION_CHOICES = [
    app_commands.Choice(name=value.title(), value=value)
    for value in ESCALATION_ACTIONS
]


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    automod = app_commands.Group(
        name="automod",
        description="Configure automatic moderation",
    )

    @automod.command(name="rule", description="Enable or configure an AutoMod filter")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(filter_type=FILTER_CHOICES, action=ACTION_CHOICES)
    async def rule(
        self,
        interaction: discord.Interaction,
        filter_type: app_commands.Choice[str],
        enabled: bool,
        threshold: app_commands.Range[int, 1, 100000],
        action: app_commands.Choice[str],
        timeout_seconds: app_commands.Range[int, 1, 2419200] = 300,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        try:
            await AutoModService(self.bot.db, self.bot.cache).configure_rule(
                interaction.guild.id,
                filter_type.value,
                enabled=enabled,
                threshold=threshold,
                action=action.value,
                duration_seconds=timeout_seconds,
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await interaction.response.send_message(
            f"{filter_type.name} is {'enabled' if enabled else 'disabled'} "
            f"(threshold {threshold}, action {action.value}).",
            ephemeral=True,
        )

    @automod.command(name="exempt-role", description="Exempt or include a role")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(filter_type=FILTER_CHOICES)
    async def exempt_role(
        self,
        interaction: discord.Interaction,
        filter_type: app_commands.Choice[str],
        role: discord.Role,
        exempt: bool,
    ):
        await self._set_exemption(
            interaction,
            filter_type.value,
            role.id,
            channel=False,
            exempt=exempt,
        )

    @automod.command(name="exempt-channel", description="Exempt or include a channel")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(filter_type=FILTER_CHOICES)
    async def exempt_channel(
        self,
        interaction: discord.Interaction,
        filter_type: app_commands.Choice[str],
        channel: discord.TextChannel,
        exempt: bool,
    ):
        await self._set_exemption(
            interaction,
            filter_type.value,
            channel.id,
            channel=True,
            exempt=exempt,
        )

    async def _set_exemption(
        self,
        interaction,
        rule_type,
        value,
        *,
        channel,
        exempt,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        await AutoModService(self.bot.db, self.bot.cache).set_exemption(
            interaction.guild.id,
            rule_type,
            value=value,
            channel=channel,
            exempt=exempt,
        )
        await interaction.response.send_message(
            f"AutoMod exemption {'added' if exempt else 'removed'}.",
            ephemeral=True,
        )

    @automod.command(name="word", description="Add or remove a blocked word")
    @app_commands.default_permissions(administrator=True)
    async def word(
        self,
        interaction: discord.Interaction,
        word: str,
        enabled: bool,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        try:
            await AutoModService(self.bot.db, self.bot.cache).configure_word(
                interaction.guild.id,
                word,
                enabled,
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await interaction.response.send_message(
            f"`{word.strip()}` {'added to' if enabled else 'removed from'} blocked words.",
            ephemeral=True,
        )

    @automod.command(name="link-domain", description="Allow or deny a link domain")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(mode=[
        app_commands.Choice(name="Allow", value="allow"),
        app_commands.Choice(name="Deny", value="deny"),
    ])
    async def link_domain(
        self,
        interaction: discord.Interaction,
        domain: str,
        mode: app_commands.Choice[str],
        enabled: bool,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        try:
            await AutoModService(self.bot.db, self.bot.cache).configure_link_domain(
                interaction.guild.id,
                domain,
                mode.value,
                enabled,
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await interaction.response.send_message(
            f"Link domain `{domain}` {mode.value} rule updated.",
            ephemeral=True,
        )

    @automod.command(name="escalation", description="Set a violation escalation")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(filter_type=FILTER_CHOICES, action=ESCALATION_CHOICES)
    async def escalation(
        self,
        interaction: discord.Interaction,
        filter_type: app_commands.Choice[str],
        threshold: app_commands.Range[int, 1, 100],
        action: app_commands.Choice[str],
        enabled: bool,
        window_hours: app_commands.Range[int, 1, 744] = 168,
        timeout_seconds: app_commands.Range[int, 1, 2419200] = 300,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        try:
            await AutoModService(self.bot.db, self.bot.cache).set_escalation(
                interaction.guild.id,
                filter_type.value,
                threshold=threshold,
                action=action.value,
                duration_seconds=timeout_seconds,
                enabled=enabled,
                window_seconds=window_hours * 3600,
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await interaction.response.send_message(
            f"Escalation {('configured' if enabled else 'removed')} "
            f"for {filter_type.name}.",
            ephemeral=True,
        )

    # Message inspection has exactly one owner: Bot.process_message. A second
    # on_message listener here used to apply the same rules twice with a
    # per-message service instance, so spam windows never accumulated and a
    # member could be punished multiple times for one message.

    @automod.command(name="status", description="Show AutoMod status and configured filters")
    @app_commands.default_permissions(manage_guild=True)
    async def status(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.", ephemeral=True
            )
            return
        config = await self.bot.guild_config.get(interaction.guild.id)
        rules = await self._service().rules(interaction.guild.id)
        enabled = bool((config or {}).get("automod_enabled"))
        embed = discord.Embed(
            title="AutoMod status",
            colour=discord.Colour.blurple(),
            description=(
                f"**Global AutoMod:** {'enabled' if enabled else 'disabled'}\n"
                f"**Configured filters:** {len(rules)}"
            ),
        )
        if rules:
            lines = []
            for rule in rules:
                state = "on" if rule.enabled else "off"
                threshold = (rule.config or {}).get("threshold", "—")
                lines.append(
                    f"`{rule.name}` — {state} · action `{rule.action}` · threshold `{threshold}`"
                )
            embed.add_field(name="Filters", value="\n".join(lines)[:1024], inline=False)
        else:
            embed.add_field(
                name="Filters",
                value="No filters configured. Use `/automod rule` to create one.",
                inline=False,
            )
        embed.set_footer(text="Message checks run once per message in the main event pipeline.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @automod.command(name="toggle", description="Enable or disable AutoMod for this server")
    @app_commands.default_permissions(administrator=True)
    async def toggle(self, interaction: discord.Interaction, enabled: bool):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.", ephemeral=True
            )
            return
        await self.bot.guild_config.update(
            interaction.guild.id, automod_enabled=enabled
        )
        await interaction.response.send_message(
            f"AutoMod is now **{'enabled' if enabled else 'disabled'}**. "
            "Individual filters still need to be enabled with `/automod rule`.",
            ephemeral=True,
        )

    def _service(self):
        service = getattr(self.bot, "automod_filters", None)
        return service or AutoModService(self.bot.db, self.bot.cache)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))

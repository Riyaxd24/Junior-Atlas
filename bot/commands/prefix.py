import discord
from discord import app_commands
from discord.ext import commands


class Prefix(commands.Cog):
    """Per-server prefix configuration."""

    config = app_commands.Group(
        name="config",
        description="Configure Junior Atlas for this server",
    )

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="prefix", invoke_without_command=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        """Show this server's command prefix."""
        config = await self.bot.guild_config.get(ctx.guild.id)
        current = (config or {}).get("command_prefix") or ","
        await ctx.send(f"Current prefix: `{discord.utils.escape_markdown(current)}`")

    @prefix.command(name="set", description="Set this server's command prefix")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx, prefix: str):
        prefix = prefix.strip()
        if not prefix or len(prefix) > 5 or any(char.isspace() for char in prefix):
            await ctx.send("Choose a prefix between 1 and 5 characters with no spaces.")
            return
        if prefix.startswith("<@") or prefix.startswith("<#"):
            await ctx.send("Mentions cannot be used as a command prefix.")
            return
        await self.bot.guild_config.update(ctx.guild.id, command_prefix=prefix)
        await ctx.send(
            f"Prefix updated to `{discord.utils.escape_markdown(prefix)}`. "
            "Commands will now use the new prefix."
        )

    @prefix.command(name="reset", description="Reset this server's prefix to the default")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reset_prefix(self, ctx):
        await self.bot.guild_config.update(ctx.guild.id, command_prefix=",")
        await ctx.send("Prefix reset to `,`.")

    @config.command(name="show", description="Show core guild settings")
    @app_commands.default_permissions(manage_guild=True)
    async def show_config(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        settings = await self.bot.guild_config.get(interaction.guild.id)
        log_channel_id = settings.get("log_channel_id")
        mod_role_id = settings.get("mod_role_id")
        embed = discord.Embed(
            title="Guild configuration",
            description=(
                f"Prefix: `{settings.get('command_prefix') or ','}`\n"
                f"Timezone: `{settings.get('timezone') or 'UTC'}`"
            ),
            colour=discord.Colour(0x5865F2),
        )
        embed.add_field(
            name="Moderation log",
            value=f"<#{log_channel_id}>" if log_channel_id else "Not configured",
            inline=True,
        )
        embed.add_field(
            name="Moderation role",
            value=f"<@&{mod_role_id}>" if mod_role_id else "Not configured",
            inline=True,
        )
        embed.set_footer(text="Junior Atlas")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @config.command(name="prefix", description="Set this server's text-command prefix")
    @app_commands.default_permissions(manage_guild=True)
    async def set_config_prefix(
        self,
        interaction: discord.Interaction,
        prefix: str,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        prefix = prefix.strip()
        if not prefix or len(prefix) > 5 or any(char.isspace() for char in prefix):
            await interaction.response.send_message(
                "Choose a prefix between 1 and 5 characters with no spaces.",
                ephemeral=True,
            )
            return
        await self.bot.guild_config.update(
            interaction.guild.id,
            command_prefix=prefix,
        )
        await interaction.response.send_message(
            f"Text-command prefix set to `{discord.utils.escape_markdown(prefix)}`.",
            ephemeral=True,
        )

    @config.command(name="mod-log", description="Set the moderation log channel")
    @app_commands.default_permissions(manage_guild=True)
    async def set_mod_log(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        await self.bot.guild_config.update(
            interaction.guild.id,
            log_channel_id=channel.id,
        )
        await interaction.response.send_message(
            f"Moderation log channel set to {channel.mention}.",
            ephemeral=True,
        )

    @config.command(name="mod-role", description="Set the configured moderation role")
    @app_commands.default_permissions(manage_guild=True)
    async def set_mod_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in a server.",
                ephemeral=True,
            )
            return
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(
                "That role is not below my highest role.",
                ephemeral=True,
            )
            return
        await self.bot.guild_config.update(
            interaction.guild.id,
            mod_role_id=role.id,
        )
        await interaction.response.send_message(
            f"Moderation role set to {role.mention}.",
            ephemeral=True,
        )

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need **Manage Server** permission to change the prefix.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: `prefix set <new-prefix>`")
            return
        raise error


async def setup(bot):
    await bot.add_cog(Prefix(bot))

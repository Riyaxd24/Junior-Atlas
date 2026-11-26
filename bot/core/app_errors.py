import logging

import discord
from discord import app_commands

from bot.core.interactions import is_expired_interaction, safe_send

log = logging.getLogger("bot.commands")


class PermissionDenied(Exception):
    """Raised when a configured or Discord permission check fails."""


def _message(error: app_commands.AppCommandError) -> str:
    if isinstance(error, app_commands.errors.MissingPermissions):
        return "You don't have permission to use this command."
    if isinstance(error, app_commands.errors.BotMissingPermissions):
        return "I don't have the Discord permissions required for that action."
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        return f"Please wait **{error.retry_after:.1f}s** before trying again."
    if isinstance(error, app_commands.errors.TransformerError):
        return "One of the supplied values is invalid. Please check the command options."
    if isinstance(error, app_commands.errors.CheckFailure):
        return "This command cannot be used here or with your current permissions."
    return "Something went wrong while running that command. The error has been logged."


def _command_name(interaction: discord.Interaction) -> str:
    command = getattr(interaction, "command", None)
    return str(
        getattr(command, "qualified_name", None)
        or getattr(command, "name", None)
        or "unknown"
    )


async def handle_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    original = getattr(error, "original", error)
    if is_expired_interaction(original) or is_expired_interaction(error):
        log.debug(
            "application interaction expired guild=%s command=%s",
            getattr(interaction.guild, "id", None),
            _command_name(interaction),
        )
        return
    if not isinstance(error, (app_commands.errors.MissingPermissions,
                              app_commands.errors.BotMissingPermissions,
                              app_commands.errors.CommandOnCooldown,
                              app_commands.errors.TransformerError,
                              app_commands.errors.CheckFailure)):
        log.error(
            "application command failed command=%s error_type=%s guild=%s user=%s",
            _command_name(interaction),
            type(original).__name__,
            getattr(getattr(interaction, "guild", None), "id", None),
            getattr(getattr(interaction, "user", None), "id", None),
            exc_info=(type(original), original, original.__traceback__),
        )
    embed = discord.Embed(title="✕ Command failed", description=_message(error), colour=discord.Colour.red())
    embed.set_footer(text="Junior Atlas • Try /help for command usage")
    await safe_send(interaction, embed=embed, ephemeral=True)

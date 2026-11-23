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


async def handle_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    original = getattr(error, "original", error)
    if is_expired_interaction(original) or is_expired_interaction(error):
        log.debug(
            "application interaction expired guild=%s",
            getattr(interaction.guild, "id", None),
        )
        return
    if not isinstance(error, (app_commands.errors.MissingPermissions,
                              app_commands.errors.BotMissingPermissions,
                              app_commands.errors.CommandOnCooldown,
                              app_commands.errors.TransformerError,
                              app_commands.errors.CheckFailure)):
        log.error(
            "application command failed",
            exc_info=(type(original), original, original.__traceback__),
        )
    embed = discord.Embed(title="✕ Command failed", description=_message(error), colour=discord.Colour.red())
    embed.set_footer(text="Junior Atlas • Try /help for command usage")
    await safe_send(interaction, embed=embed, ephemeral=True)

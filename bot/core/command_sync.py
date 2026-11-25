"""Application-command registration and synchronization helpers.

Discord slash commands are generated from callback signatures.  A callback
declared as ``async def hug(ctx, member=None)`` therefore exposes an unwanted
``ctx`` option.  This module validates the local tree before synchronization and
performs a deterministic sync that also removes obsolete definitions owned by
this application.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator

import discord
from discord import app_commands

log = logging.getLogger("bot.command_sync")

# Parameters that are never user-facing slash-command options.
FORBIDDEN_OPTION_NAMES = frozenset({"ctx", "self", "interaction", "cog", "bot"})

# Discord rejects an application-command option with more than 25 static choices.
MAX_STATIC_CHOICES = 25


def iter_app_commands(commands: Iterable) -> Iterator:
    """Yield every command, including nested subcommands and groups."""
    for command in commands:
        yield command
        children = getattr(command, "commands", None)
        if children:
            yield from iter_app_commands(children)


def command_problems(tree: app_commands.CommandTree) -> list[str]:
    """Return human-readable registration problems for the local tree."""
    problems: list[str] = []
    seen: set[str] = set()
    for command in iter_app_commands(tree.get_commands()):
        qualified = getattr(command, "qualified_name", command.name)
        if qualified in seen:
            problems.append(f"duplicate application command: {qualified}")
        seen.add(qualified)
        for parameter in getattr(command, "parameters", []):
            name = getattr(parameter, "name", "")
            if name in FORBIDDEN_OPTION_NAMES:
                problems.append(
                    f"{qualified} exposes internal parameter '{name}' as a slash option"
                )
            if name.startswith("_"):
                problems.append(
                    f"{qualified} exposes private parameter '{name}' as a slash option"
                )
            choices = getattr(parameter, "choices", []) or []
            if len(choices) > MAX_STATIC_CHOICES:
                problems.append(
                    f"{qualified} parameter '{name}' declares {len(choices)} static "
                    f"choices; Discord allows at most {MAX_STATIC_CHOICES}. "
                    "Use autocomplete instead of removing actions."
                )
    return problems


async def _sync_scope(tree: app_commands.CommandTree, scope: str, **kwargs) -> list:
    """Run one sync scope and make failures impossible to miss in the logs."""
    try:
        synced = await tree.sync(**kwargs)
    except app_commands.CommandSyncFailure as error:
        # discord.py includes the offending command and parameter in the
        # exception text.  Log every line so the actionable detail is never
        # hidden inside a multi-line traceback, then re-raise: a failed sync
        # must stop startup rather than be reported as success.
        log.error(
            "Discord application command sync FAILED scope=%s. "
            "Fix the command definition below and restart; startup will stop.",
            scope,
        )
        for line in str(error).splitlines():
            log.error("Discord command sync detail scope=%s: %s", scope, line)
        raise
    except Exception:
        log.exception(
            "Discord application command sync FAILED scope=%s. Startup will stop.",
            scope,
        )
        raise

    log.info(
        "Discord command sync succeeded scope=%s commands=%d",
        scope,
        len(synced),
    )
    return synced


async def sync_application_commands(
    tree: app_commands.CommandTree,
    *,
    guild_id: int | None = None,
) -> tuple[list, list | None]:
    """Synchronize the global tree and, when configured, a guild copy.

    A global sync is always performed first.  Discord removes global commands
    that are no longer in the tree, which clears definitions left behind by an
    older release (most notably the historical ``ctx`` option).  When a guild
    ID is configured we additionally copy and sync to that guild so updated
    commands appear immediately during development.

    This is a *definition* sync, not a blind command wipe: unrelated
    application commands and all local cogs remain registered.
    """
    global_synced = await _sync_scope(tree, "global")
    guild_synced: list | None = None
    if guild_id:
        guild = discord.Object(id=guild_id)
        tree.copy_global_to(guild=guild)
        guild_synced = await _sync_scope(tree, f"guild:{guild_id}", guild=guild)
    return global_synced, guild_synced

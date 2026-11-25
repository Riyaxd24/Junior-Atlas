"""Application-command registration and synchronization helpers.

Discord slash commands are generated from callback signatures.  A callback
declared as ``async def hug(ctx, member=None)`` therefore exposes an unwanted
``ctx`` option.  This module validates the local tree before synchronization and
performs a deterministic sync that also removes obsolete definitions owned by
this application.

Command registration policy
---------------------------
Application commands are owned by exactly one scope: **global**.  A global
sync is authoritative and atomically replaces this application's global command
set, so removed/renamed commands disappear from Discord.  A configured guild is
only used to *clean up* guild-scoped definitions left by older releases; global
commands are never copied into the guild.  Registering the same tree both
globally and in a guild makes Discord display two entries for every command.
"""
from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Iterable, Iterator

import discord
from discord import app_commands

log = logging.getLogger("bot.command_sync")

# Parameters that are never user-facing slash-command options.
FORBIDDEN_OPTION_NAMES = frozenset({"ctx", "self", "interaction", "cog", "bot"})

# Discord rejects an application-command option with more than 25 static choices.
MAX_STATIC_CHOICES = 25

# Discord allows at most this many root application commands per scope.
MAX_ROOT_COMMANDS = 100

# Deployment metadata environment variables, most specific first.
_DEPLOYMENT_KEYS = (
    "GIT_COMMIT",
    "GIT_COMMIT_SHA",
    "RAILWAY_GIT_COMMIT_SHA",
    "SOURCE_VERSION",
    "COMMIT_SHA",
    "RELEASE",
    "APP_VERSION",
)


def deployment_version() -> str:
    """Return the deployment commit/version for startup diagnostics."""
    for key in _DEPLOYMENT_KEYS:
        value = os.getenv(key, "").strip()
        if value:
            return value
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    commit = result.stdout.strip()
    return commit or "unknown"


def iter_app_commands(commands: Iterable) -> Iterator:
    """Yield every command, including nested subcommands and groups."""
    for command in commands:
        yield command
        children = getattr(command, "commands", None)
        if children:
            yield from iter_app_commands(children)


def iter_command_scopes(tree: app_commands.CommandTree) -> Iterator[tuple[str, list]]:
    """Yield ``(scope_label, commands)`` for the global and guild scopes.

    ``discord.py`` stores guild-scoped commands in the private
    ``_guild_commands`` mapping.  Reading it here lets validation catch a tree
    that was accidentally copied into a guild before synchronization.
    """
    yield "global", list(tree.get_commands())
    for guild_id, mapping in getattr(tree, "_guild_commands", {}).items():
        yield f"guild:{guild_id}", list(mapping.values())


def command_problems(tree: app_commands.CommandTree) -> list[str]:
    """Return human-readable registration problems for the local tree.

    Validation is performed per scope.  The same qualified command name may not
    occur twice in one scope, and it may not be registered in both the global
    and a guild scope: that is exactly how the duplicate slash-command entries
    were produced.
    """
    problems: list[str] = []
    scope_names: dict[str, set[str]] = {}

    for scope, commands in iter_command_scopes(tree):
        seen: set[str] = set()
        roots = list(commands)
        if len(roots) > MAX_ROOT_COMMANDS:
            problems.append(
                f"{scope} declares {len(roots)} root application commands; "
                f"Discord allows at most {MAX_ROOT_COMMANDS}."
            )
        for command in iter_app_commands(commands):
            qualified = getattr(command, "qualified_name", command.name)
            if qualified in seen:
                problems.append(
                    f"duplicate application command in {scope}: {qualified}"
                )
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
        scope_names[scope] = seen

    global_names = scope_names.get("global", set())
    for scope, names in scope_names.items():
        if scope == "global":
            continue
        overlap = global_names & names
        if overlap:
            problems.append(
                f"application commands registered in both global and {scope}: "
                f"{', '.join(sorted(overlap))}. Register each command in exactly "
                "one scope."
            )
    return problems


def _guild_commands(tree, guild) -> list:
    getter = getattr(tree, "get_commands", None)
    if getter is None:
        return []
    try:
        return list(getter(guild=guild))
    except TypeError:
        return []


def prune_guild_duplicates(tree: app_commands.CommandTree, guild: discord.abc.Snowflake) -> list[str]:
    """Remove local guild definitions that shadow a global command.

    Intentional guild-only commands (names that do not exist globally) are kept.
    The subsequent guild sync then removes the same stale definitions remotely.
    """
    getter = getattr(tree, "get_commands", None)
    if getter is None:
        return []
    global_names = {
        getattr(command, "name", "")
        for command in getter()
    }
    removed: list[str] = []
    remover = getattr(tree, "remove_command", None)
    if remover is None:
        return removed
    for command in _guild_commands(tree, guild):
        if command.name in global_names:
            remover(command.name, guild=guild)
            removed.append(command.name)
    return removed


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
    """Synchronize the application command tree using one intended scope.

    The global tree is always synced first.  Discord replaces this
    application's global command set with the payload, which removes global
    definitions left behind by an older release (for example the historical
    ``ctx`` option) without touching other applications.

    When ``guild_id`` is configured, guild-scoped duplicates are removed
    locally and the guild scope is synced as well.  Global commands are **not**
    copied into the guild; the guild sync normally sends an empty set, which
    deletes the stale guild copies created by previous releases.  Guild-only
    command definitions that do not shadow a global command are preserved.

    Returns ``(global_synced, guild_synced)``.  ``guild_synced`` is ``None``
    when no guild cleanup was requested.
    """
    log.info(
        "Syncing application commands strategy=global-only application_id=%s "
        "deployment=%s",
        getattr(getattr(tree, "client", None), "application_id", None),
        deployment_version(),
    )

    global_synced = await _sync_scope(tree, "global")

    guild_synced: list | None = None
    if guild_id:
        guild = discord.Object(id=guild_id)
        removed = prune_guild_duplicates(tree, guild)
        if removed:
            log.info(
                "Removed duplicate guild-scoped command definitions scope=guild:%s "
                "commands=%s",
                guild_id,
                sorted(removed),
            )
        guild_synced = await _sync_scope(tree, f"guild:{guild_id}", guild=guild)
        log.info(
            "Guild scope cleaned; global commands are not copied into guild=%s "
            "remaining_guild_only=%s",
            guild_id,
            sorted(command.name for command in _guild_commands(tree, guild)),
        )
    return global_synced, guild_synced

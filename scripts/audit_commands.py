"""Inspect live Discord application command registrations.

This is the operator-side companion to ``bot.core.command_sync``.  It reports
the bot application ID, deployment version, global commands, guild commands,
and any command names that exist in both scopes.  Cleanup is opt-in and only
removes this application's stale guild-scoped commands.

Examples::

    DISCORD_TOKEN=... GUILD_ID=... python -m scripts.audit_commands
    DISCORD_TOKEN=... GUILD_ID=... python -m scripts.audit_commands \
        --cleanup-guild-duplicates
    DISCORD_TOKEN=... GUILD_ID=... python -m scripts.audit_commands \
        --check-local

``--cleanup-guild-duplicates`` deletes guild commands whose names are also
registered globally.  ``--cleanup-guild-all`` deletes every guild command owned
by this application in the target guild; use it only when the intended scope is
global-only.  Neither option touches global commands or other applications.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
from collections import Counter

import discord

from bot.core.command_sync import deployment_version


def _names(commands) -> list[str]:
    return sorted(command["name"] for command in commands)


def _duplicates(names: list[str]) -> list[str]:
    return sorted(name for name, count in Counter(names).items() if count > 1)


def _print_commands(label: str, commands) -> None:
    print(f"{label}: {len(commands)}")
    for command in sorted(commands, key=lambda item: item["name"]):
        options = command.get("options") or []
        subcommands = [
            option["name"]
            for option in options
            if option.get("type") in {1, 2}
        ]
        detail = f" subcommands={subcommands}" if subcommands else ""
        print(
            f"  id={command['id']} name=/{command['name']} "
            f"type={command.get('type', 1)}{detail}"
        )


async def _load_local_tree(token: str):
    from bot.core.bot import EXTENSIONS, Bot
    from bot.core.command_sync import command_problems, iter_app_commands
    from bot.core.config import Settings

    bot = Bot(Settings(token=token))
    try:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
        roots = bot.tree.get_commands()
        names = [command.name for command in roots]
        problems = command_problems(bot.tree)
        return names, problems, len(list(iter_app_commands(roots)))
    finally:
        await bot.cache.close()
        await bot.db.close()


async def _run(args) -> int:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        print("DISCORD_TOKEN is not set; cannot inspect live Discord commands.")
        return 2

    guild_id = args.guild_id or os.getenv("GUILD_ID", "").strip()
    guild_id = int(guild_id) if guild_id else None

    client = discord.Client(intents=discord.Intents.none())
    try:
        await client.login(token)
        application_id = client.application_id
        print(f"application_id={application_id}")
        print(f"application_name={client.application.name if client.application else 'unknown'}")
        print(f"deployment={deployment_version()}")
        print(f"guild_id={guild_id}")

        global_commands = await client.http.get_global_commands(application_id)
        _print_commands("global", global_commands)

        guild_commands = []
        if guild_id:
            guild_commands = await client.http.get_guild_commands(
                application_id, guild_id
            )
            _print_commands(f"guild:{guild_id}", guild_commands)

        global_names = _names(global_commands)
        guild_names = _names(guild_commands)
        overlap = sorted(set(global_names) & set(guild_names))
        print(f"global_duplicate_names={_duplicates(global_names)}")
        print(f"guild_duplicate_names={_duplicates(guild_names)}")
        print(f"global_and_guild_overlap={overlap}")

        if args.check_local:
            local_names, problems, node_count = await _load_local_tree(token)
            print(f"local_root_commands={len(local_names)} local_nodes={node_count}")
            print(f"local_validation_problems={problems}")
            missing = sorted(set(local_names) - set(global_names))
            extra = sorted(set(global_names) - set(local_names))
            print(f"missing_from_discord_global={missing}")
            print(f"extra_on_discord_global={extra}")

        if guild_id and args.cleanup_guild_duplicates:
            stale = [
                command
                for command in guild_commands
                if command["name"] in set(global_names)
            ]
            for command in stale:
                await client.http.delete_guild_command(
                    application_id, guild_id, command["id"]
                )
                print(f"deleted_guild_duplicate id={command['id']} name=/{command['name']}")
            print(f"deleted_guild_duplicates={len(stale)}")

        if guild_id and args.cleanup_guild_all:
            await client.http.bulk_upsert_guild_commands(
                application_id, guild_id, payload=[]
            )
            print(f"cleared_all_guild_commands guild={guild_id}")

        return 0
    finally:
        await client.http.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guild-id", type=int, default=None)
    parser.add_argument(
        "--check-local",
        action="store_true",
        help="load local extensions and compare the intended tree with Discord",
    )
    parser.add_argument(
        "--cleanup-guild-duplicates",
        action="store_true",
        help="delete guild commands whose names also exist globally",
    )
    parser.add_argument(
        "--cleanup-guild-all",
        action="store_true",
        help="delete every guild command owned by this application in the guild",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())

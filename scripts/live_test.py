"""Opt-in live Discord smoke tests for Junior Atlas.

Live checks are deliberately conservative.  They never ban, kick, delete guild
resources, or send ``@everyone``/``@here``.  Anti-nuke and destructive AutoMod
triggers are refused here and must be exercised with unit tests/mocks.

Examples::

    DISCORD_TOKEN=... TEST_GUILD_ID=... EXPECTED_APPLICATION_ID=... \
        python -m scripts.live_test --live
    DISCORD_TOKEN=... TEST_GUILD_ID=... EXPECTED_APPLICATION_ID=... \
        python -m scripts.live_test --live --test-channel-id 123 \
        --send-test-message

A missing ``--live`` reports ``NOT RUN`` instead of connecting.
"""
from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT RUN"


@dataclass(frozen=True)
class Check:
    name: str
    status: Status
    detail: str = ""


# Never include a user/role/everyone mention in the live test message.
SAFE_TEST_MESSAGE = "Junior Atlas live smoke test. No mentions were used."
REQUIRED_GLOBAL_COMMANDS = frozenset(
    {"ping", "help", "action", "automod", "rules", "security"}
)


def preflight(
    *,
    live: bool,
    token: str,
    guild_id: int | None,
    expected_application_id: int | None,
    destructive: bool = False,
) -> list[Check]:
    """Validate the request before any network connection is attempted."""
    checks: list[Check] = [
        Check(
            "live-mode",
            Status.PASS if live else Status.NOT_RUN,
            "--live was supplied."
            if live
            else "Pass --live to run live Discord checks.",
        )
    ]
    if not live:
        checks.extend(
            [
                Check("token", Status.NOT_RUN, "Live checks were not requested."),
                Check("test-guild", Status.NOT_RUN, "Live checks were not requested."),
                Check(
                    "expected-application-id",
                    Status.NOT_RUN,
                    "Live checks were not requested.",
                ),
            ]
        )
        return checks

    checks.append(
        Check(
            "token",
            Status.PASS if token else Status.FAIL,
            "DISCORD_TOKEN is set." if token else "DISCORD_TOKEN is not set.",
        )
    )
    checks.append(
        Check(
            "test-guild",
            Status.PASS if guild_id else Status.FAIL,
            f"Test guild id={guild_id}."
            if guild_id
            else "Set TEST_GUILD_ID or pass --guild-id.",
        )
    )
    checks.append(
        Check(
            "expected-application-id",
            Status.PASS if expected_application_id else Status.FAIL,
            f"Expected application id={expected_application_id}."
            if expected_application_id
            else "Set EXPECTED_APPLICATION_ID or pass --expected-application-id.",
        )
    )
    checks.append(
        Check(
            "destructive-tests",
            Status.FAIL if destructive else Status.PASS,
            "Destructive live tests are refused; use unit tests/mocks."
            if destructive
            else "No destructive live tests requested.",
        )
    )
    return checks


def _safe_name(value) -> str:
    return repr(str(value))[:80]


async def run_live_checks(
    *,
    token: str,
    guild_id: int,
    expected_application_id: int,
    test_channel_id: int | None = None,
    send_test_message: bool = False,
) -> list[Check]:
    """Connect read-only and run safe live checks.  No destructive action runs."""
    import discord

    checks: list[Check] = []
    client = discord.Client(intents=discord.Intents.none())
    try:
        await client.login(token)
        application_id = client.application_id
        checks.append(
            Check(
                "application-id",
                Status.PASS
                if application_id == expected_application_id
                else Status.FAIL,
                f"application_id={application_id} expected={expected_application_id}",
            )
        )

        guild = client.get_guild(guild_id)
        if guild is None:
            try:
                guild = await client.fetch_guild(guild_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
                guild = None
                checks.append(
                    Check(
                        "guild-access",
                        Status.FAIL,
                        f"Could not access guild {guild_id}: {type(exc).__name__}",
                    )
                )
        if guild is not None:
            checks.append(
                Check(
                    "guild-access",
                    Status.PASS,
                    f"guild={guild.id} name={_safe_name(guild.name)}",
                )
            )

        if guild is not None:
            try:
                commands = await client.http.get_global_commands(application_id)
            except discord.HTTPException as exc:
                commands = []
                checks.append(
                    Check(
                        "global-command-sync",
                        Status.FAIL,
                        f"Could not list global commands: {type(exc).__name__}",
                    )
                )
            if commands or not any(c.name == "global-command-sync" for c in checks):
                names = {command["name"] for command in commands}
                missing = sorted(REQUIRED_GLOBAL_COMMANDS - names)
                checks.append(
                    Check(
                        "global-command-sync",
                        Status.PASS if not missing else Status.FAIL,
                        "All expected commands are registered."
                        if not missing
                        else f"Missing global commands: {missing}",
                    )
                )

            me = None
            try:
                me = await guild.fetch_member(application_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                me = None
            if me is None:
                checks.append(
                    Check(
                        "bot-permissions",
                        Status.FAIL,
                        "Could not resolve the bot member in the test guild.",
                    )
                )
            else:
                permissions = me.guild_permissions
                required = (
                    "view_channel",
                    "send_messages",
                    "embed_links",
                    "read_message_history",
                )
                missing = [
                    name
                    for name in required
                    if not getattr(permissions, name, False)
                ]
                checks.append(
                    Check(
                        "bot-permissions",
                        Status.PASS if not missing else Status.FAIL,
                        "Required channel permissions are present."
                        if not missing
                        else f"Missing permissions: {missing}",
                    )
                )
        else:
            checks.extend(
                [
                    Check(
                        "global-command-sync",
                        Status.NOT_RUN,
                        "Guild access failed, so command checks were skipped.",
                    ),
                    Check(
                        "bot-permissions",
                        Status.NOT_RUN,
                        "Guild access failed, so permission checks were skipped.",
                    ),
                ]
            )

        if not send_test_message or test_channel_id is None:
            checks.append(
                Check(
                    "isolated-channel-message",
                    Status.NOT_RUN,
                    "Pass --send-test-message and --test-channel-id to send one "
                    "safe, mention-free message.",
                )
            )
        elif guild is not None:
            channel = guild.get_channel(test_channel_id)
            if channel is None:
                try:
                    channel = await client.fetch_channel(test_channel_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    channel = None
            if channel is None:
                checks.append(
                    Check(
                        "isolated-channel-message",
                        Status.FAIL,
                        f"Could not resolve test channel {test_channel_id}.",
                    )
                )
            elif getattr(getattr(channel, "guild", None), "id", None) != guild.id:
                checks.append(
                    Check(
                        "isolated-channel-message",
                        Status.FAIL,
                        "The test channel is not in the configured test guild.",
                    )
                )
            else:
                try:
                    message = await channel.send(
                        SAFE_TEST_MESSAGE,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except discord.HTTPException as exc:
                    checks.append(
                        Check(
                            "isolated-channel-message",
                            Status.FAIL,
                            f"Send failed: {type(exc).__name__}",
                        )
                    )
                else:
                    checks.append(
                        Check(
                            "isolated-channel-message",
                            Status.PASS,
                            f"message_id={message.id} channel={channel.id}",
                        )
                    )

        # These require a second non-bot account or destructive actions, so they
        # are intentionally never executed by this script.
        checks.extend(
            [
                Check(
                    "automod-live",
                    Status.NOT_RUN,
                    "Requires a second non-bot account in an isolated channel; "
                    "covered by simulated AutoMod tests.",
                ),
                Check(
                    "anti-nuke-live",
                    Status.NOT_RUN,
                    "Destructive triggers are refused; covered by unit tests and mocks.",
                ),
                Check(
                    "mass-ping-live",
                    Status.NOT_RUN,
                    "No @everyone/@here is sent; covered by simulated mention tests.",
                ),
                Check(
                    "slash-invocation-live",
                    Status.NOT_RUN,
                    "Bots cannot invoke their own slash commands; registration is checked.",
                ),
            ]
        )
        return checks
    finally:
        try:
            await client.close()
        except Exception:
            pass


def print_report(checks: list[Check]) -> None:
    for check in checks:
        detail = f" — {check.detail}" if check.detail else ""
        print(f"[{check.status.value}] {check.name}{detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="run live Discord checks")
    parser.add_argument("--guild-id", type=int, default=None)
    parser.add_argument("--expected-application-id", type=int, default=None)
    parser.add_argument("--test-channel-id", type=int, default=None)
    parser.add_argument(
        "--send-test-message",
        action="store_true",
        help="send one safe, mention-free message to --test-channel-id",
    )
    parser.add_argument(
        "--destructive",
        action="store_true",
        help="refused: destructive live tests are not supported",
    )
    args = parser.parse_args(argv)

    token = os.getenv("DISCORD_TOKEN", "").strip()
    raw_guild_id = (
        args.guild_id
        or os.getenv("TEST_GUILD_ID")
        or os.getenv("GUILD_ID")
        or ""
    )
    raw_application_id = (
        args.expected_application_id
        or os.getenv("EXPECTED_APPLICATION_ID")
        or ""
    )
    try:
        guild_id = int(raw_guild_id) if str(raw_guild_id).strip() else None
    except ValueError:
        guild_id = None
    try:
        expected_application_id = (
            int(raw_application_id) if str(raw_application_id).strip() else None
        )
    except ValueError:
        expected_application_id = None

    checks = preflight(
        live=args.live,
        token=token,
        guild_id=guild_id,
        expected_application_id=expected_application_id,
        destructive=args.destructive,
    )

    can_connect = (
        args.live
        and token
        and guild_id
        and expected_application_id
        and not args.destructive
    )
    if can_connect:
        try:
            live_checks = asyncio.run(
                run_live_checks(
                    token=token,
                    guild_id=guild_id,
                    expected_application_id=expected_application_id,
                    test_channel_id=args.test_channel_id,
                    send_test_message=args.send_test_message,
                )
            )
        except Exception as exc:  # noqa: BLE001 - report only the error type
            checks.append(
                Check(
                    "live-connection",
                    Status.FAIL,
                    f"Live connection failed: {type(exc).__name__}",
                )
            )
        else:
            checks.extend(live_checks)

    print_report(checks)
    if any(check.status is Status.FAIL for check in checks):
        return 1
    if not args.live:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

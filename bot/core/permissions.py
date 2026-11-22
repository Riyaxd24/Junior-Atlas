from __future__ import annotations

import discord

from bot.core.app_errors import PermissionDenied


def check_hierarchy(
    moderator: discord.Member,
    target: discord.Member,
    bot_member: discord.Member | None = None,
) -> None:
    if moderator.guild.owner_id == target.id:
        raise PermissionDenied("You cannot moderate the server owner.")
    if moderator.id == target.id:
        raise PermissionDenied("You cannot moderate yourself.")
    if moderator.id != moderator.guild.owner_id and moderator.top_role <= target.top_role:
        raise PermissionDenied("Your highest role is not above the target member.")
    if bot_member is not None and bot_member.top_role <= target.top_role:
        raise PermissionDenied("My highest role is not above the target member.")


def check_bot_permissions(
    target: discord.abc.GuildChannel | discord.Guild,
    bot_member: discord.Member,
    **required: bool,
) -> None:
    permissions = (
        bot_member.guild_permissions
        if isinstance(target, discord.Guild)
        else target.permissions_for(bot_member)
    )
    missing = [
        name
        for name, enabled in required.items()
        if enabled and not getattr(permissions, name, False)
    ]
    if missing:
        names = ", ".join(name.replace("_", " ").title() for name in missing)
        raise PermissionDenied(f"I am missing the required permission(s): {names}")


def check_user_permissions(
    target: discord.abc.GuildChannel | discord.Guild,
    member: discord.Member,
    **required: bool,
) -> None:
    if member.guild.owner_id == member.id or member.guild_permissions.administrator:
        return
    permissions = (
        member.guild_permissions
        if isinstance(target, discord.Guild)
        else target.permissions_for(member)
    )
    missing = [
        name
        for name, enabled in required.items()
        if enabled and not getattr(permissions, name, False)
    ]
    if missing:
        names = ", ".join(name.replace("_", " ").title() for name in missing)
        raise PermissionDenied(f"You are missing the required permission(s): {names}")

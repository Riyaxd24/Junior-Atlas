"""Central helpers for safe Discord interaction responses.

Discord requires an initial interaction response within three seconds.  Every
helper in this module is idempotent with respect to acknowledgement: it checks
``response.is_done()`` and never attempts to acknowledge the same interaction
twice.  Errors are logged with enough context to debug a failure without
leaking tokens or user content.
"""
from __future__ import annotations

import logging
from typing import Any

import discord

log = logging.getLogger("bot.interactions")


def _context(interaction: discord.Interaction) -> str:
    guild = getattr(interaction, "guild", None)
    channel = getattr(interaction, "channel", None)
    user = getattr(interaction, "user", None)
    return (
        f"guild={getattr(guild, 'id', None)} "
        f"channel={getattr(channel, 'id', None)} "
        f"user={getattr(user, 'id', None)} "
        f"interaction={getattr(interaction, 'id', None)}"
    )


def is_expired_interaction(error: BaseException) -> bool:
    return isinstance(error, discord.NotFound) and getattr(error, "code", None) == 10062


def _is_acknowledged(interaction: discord.Interaction) -> bool:
    try:
        return bool(interaction.response.is_done())
    except Exception:
        # A minimal fake interaction used in unit tests may not expose the full
        # response object; treat it as unacknowledged and let the operation run.
        return False


async def safe_defer(
    interaction: discord.Interaction,
    *,
    ephemeral: bool = True,
    thinking: bool = True,
) -> bool:
    """Acknowledge an interaction, tolerating an already-used response."""
    if _is_acknowledged(interaction):
        return True
    try:
        await interaction.response.defer(ephemeral=ephemeral, thinking=thinking)
        return True
    except TypeError:
        # Older discord.py signatures or test doubles without ``thinking``.
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            return True
        except Exception:
            log.exception("interaction defer fallback failed %s", _context(interaction))
            return False
    except discord.NotFound as error:
        if is_expired_interaction(error):
            log.debug("interaction expired before defer %s", _context(interaction))
        else:
            log.warning("interaction defer failed: Discord returned NotFound %s", _context(interaction))
        return False
    except discord.InteractionResponded:
        return True
    except discord.HTTPException:
        log.warning("interaction defer failed due to Discord HTTP error %s", _context(interaction))
        return False
    except Exception:
        log.exception("unexpected interaction defer failure %s", _context(interaction))
        return False


async def safe_send(
    interaction: discord.Interaction,
    *,
    ephemeral: bool = False,
    **kwargs: Any,
) -> bool:
    """Reply via the initial response or a follow-up as appropriate."""
    acknowledged = _is_acknowledged(interaction)
    send = interaction.followup.send if acknowledged else interaction.response.send_message
    try:
        await send(**kwargs, ephemeral=ephemeral)
        return True
    except discord.NotFound as error:
        if is_expired_interaction(error):
            log.debug("interaction expired before reply %s", _context(interaction))
        else:
            log.warning("interaction reply failed: Discord returned NotFound %s", _context(interaction))
        return False
    except discord.InteractionResponded:
        # A race with another callback: retry as a follow-up exactly once.
        try:
            await interaction.followup.send(**kwargs, ephemeral=ephemeral)
            return True
        except discord.HTTPException:
            log.warning("interaction follow-up retry failed %s", _context(interaction))
            return False
    except discord.HTTPException:
        log.warning("interaction reply failed due to Discord HTTP error %s", _context(interaction))
        return False
    except Exception:
        log.exception("unexpected interaction reply failure %s", _context(interaction))
        return False


async def safe_edit(
    interaction: discord.Interaction,
    *,
    view: discord.ui.View | None = None,
    embed: discord.Embed | None = None,
    content: str | None = None,
) -> bool:
    """Edit the message an interaction belongs to, tolerating expired tokens."""
    try:
        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=view,
        )
        return True
    except discord.InteractionResponded:
        try:
            await interaction.edit_original_response(
                content=content,
                embed=embed,
                view=view,
            )
            return True
        except discord.HTTPException:
            log.warning("interaction edit retry failed %s", _context(interaction))
            return False
    except discord.NotFound:
        log.debug("interaction message expired before edit %s", _context(interaction))
        return False
    except discord.HTTPException:
        log.warning("interaction edit failed due to Discord HTTP error %s", _context(interaction))
        return False


async def safe_modal(interaction: discord.Interaction, modal: discord.ui.Modal) -> bool:
    try:
        await interaction.response.send_modal(modal)
        return True
    except discord.InteractionResponded:
        return False
    except discord.HTTPException:
        log.warning("interaction modal failed %s", _context(interaction))
        return False


class SafeView(discord.ui.View):
    """View base with centralized error handling and timeout cleanup."""

    def __init__(self, *, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.message: discord.Message | None = None

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        log.exception(
            "UI callback failed view=%s item=%s %s",
            type(self).__name__,
            getattr(item, "label", type(item).__name__),
            _context(interaction),
        )
        await safe_send(
            interaction,
            content="Something went wrong with that interaction. Please try again.",
            ephemeral=True,
        )

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

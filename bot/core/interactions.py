from __future__ import annotations

import logging
from typing import Any

import discord


log = logging.getLogger("bot.interactions")


def is_expired_interaction(error: BaseException) -> bool:
    return isinstance(error, discord.NotFound) and getattr(error, "code", None) == 10062


async def safe_defer(interaction: discord.Interaction, *, ephemeral: bool = True) -> bool:
    if interaction.response.is_done():
        return True
    try:
        await interaction.response.defer(ephemeral=ephemeral)
        return True
    except discord.NotFound as error:
        if is_expired_interaction(error):
            log.debug("interaction expired before defer guild=%s", getattr(interaction.guild, "id", None))
        else:
            log.warning("interaction defer failed: Discord returned NotFound")
        return False
    except discord.HTTPException:
        log.warning("interaction defer failed due to Discord HTTP error")
        return False
    except Exception:
        log.exception("unexpected interaction defer failure")
        return False


async def safe_send(
    interaction: discord.Interaction,
    *,
    ephemeral: bool = False,
    **kwargs: Any,
) -> bool:
    if interaction.response.is_done():
        send = interaction.followup.send
    else:
        send = interaction.response.send_message
    try:
        await send(**kwargs, ephemeral=ephemeral)
        return True
    except discord.NotFound as error:
        if is_expired_interaction(error):
            log.debug("interaction expired before reply guild=%s", getattr(interaction.guild, "id", None))
        else:
            log.warning("interaction reply failed: Discord returned NotFound")
        return False
    except discord.HTTPException:
        log.warning("interaction reply failed due to Discord HTTP error")
        return False
    except Exception:
        log.exception("unexpected interaction reply failure")
        return False

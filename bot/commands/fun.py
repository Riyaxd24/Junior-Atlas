import inspect
import io
import logging
import math
import random
import time
from urllib.parse import urlparse

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.interactions import SafeView, safe_defer, safe_edit, safe_send
from bot.services import pixel_art
from bot.services.friendship import FriendshipXP
from bot.services.minecraft_actions import (
    ACTION_ORDER,
    MINECRAFT_ACTIONS,
    XP_COOLDOWN_SECONDS,
    action_emoji,
    action_extras,
    get_action,
)
from bot.ui import error_embed, info_embed

log = logging.getLogger(__name__)


SAFE_ACTIONS = {
    # name="fuck" is retained as a legacy safe hybrid command.
    "fuck": ("punch", "👊", "playfully punched", "playfully punched back"),
    "hug": ("hug", "🤗", "gave a hug to", "hugged back"),
    "highfive": ("highfive", "✋", "gave a high-five to", "high-fived back"),
    "fistbump": ("fistbump", "👊", "fist-bumped", "fist-bumped back"),
    "pat": ("pat", "🫳", "gave a friendly pat to", "patted back"),
    "poke": ("poke", "👉", "poked", "poked back"),
    "bonk": ("bonk", "🔨", "bonked", "bonked back"),
    "cuddle": ("cuddle", "🫂", "cuddled", "cuddled back"),
    "wave": ("wave", "👋", "waved at", "waved back at"),
    "dance": ("dance", "💃", "started dancing with", "danced along with"),
    "smile": ("smile", "😊", "shared a smile with", "smiled back"),
    "cry": ("cry", "😢", "cried dramatically near", "cried along with"),
    "shrug": ("shrug", "🤷", "shrugged at", "shrugged back at"),
    "sleep": ("sleep", "😴", "fell asleep near", "slept near"),
    "boop": ("boop", "👉", "booped", "booped back"),
    "tickle": ("tickle", "✨", "tickled", "tickled back"),
    "punch": ("punch", "👊", "landed a playful punch on", "playfully punched back"),
    "slap": ("slap", "🖐️", "playfully slapped", "playfully slapped back"),
    "bite": ("bite", "🦷", "gave a nibble to", "bit back"),
    "hold": ("hold", "🫶", "held onto", "held back"),
    "attack": ("punch", "⚔️", "launched a playful attack at", "playfully attacked back"),
    "shoot": ("punch", "💥", "fired a confetti blaster at", "fired back"),
    "bully": ("bonk", "😤", "playfully bullied", "bullied back"),
    "pout": ("pout", "😗", "pouted at", "pouted back at"),
    "blush": ("blush", "😊", "blushed at", "blushed back at"),
    "kill": ("punch", "💀", "defeated", "retaliated against"),
    "wreck": ("punch", "💥", "absolutely wrecked", "wrecked back"),
    "kiss": ("kiss", "💋", "gave an affectionate kiss to", "returned the kiss"),
    "flirt": ("flirt", "😏", "flirted with", "flirted back with"),
    "yeet": ("yeet", "🚀", "yeeted", "yeeted back"),
    "roast": ("roast", "🔥", "roasted", "roasted back"),
    "stare": ("stare", "👀", "stared at", "stared back at"),
    "facepalm": ("facepalm", "🤦", "facepalmed at", "facepalmed back at"),
    "cheer": ("cheer", "🎉", "cheered for", "cheered back for"),
    "clap": ("clap", "👏", "clapped for", "clapped back for"),
    "laugh": ("laugh", "😂", "laughed with", "laughed back with"),
    "salute": ("salute", "🎖️", "saluted", "saluted back"),
    "feed": ("feed", "🍪", "fed a cookie to", "fed a cookie back to"),
    "nom": ("nom", "😋", "nommed on", "nommed back on"),
    "comfort": ("comfort", "🫂", "comforted", "comforted back"),
    "bow": ("bow", "🙇", "bowed to", "bowed back to"),
}

# The Minecraft catalogue is the source of truth for all of its commands.
for _action_name, _action_spec in MINECRAFT_ACTIONS.items():
    SAFE_ACTIONS[_action_name] = (
        _action_spec.gif_key,
        _action_spec.emoji,
        _action_spec.initial_verb,
        _action_spec.reciprocate_verb,
    )


GIF_FALLBACKS = {
    "flirt": "blush",
    "kiss": "hug",
    "pout": "cry",
    "blush": "smile",
    "yeet": "punch",
    "roast": "slap",
    "stare": "poke",
    "facepalm": "cry",
    "cheer": "wave",
    "clap": "highfive",
    "laugh": "smile",
    "salute": "wave",
    "feed": "hug",
    "nom": "bite",
    "comfort": "hug",
    "bow": "wave",
    "boop": "poke",
    "bonk": "punch",
    "slap": "punch",
    "highfive": "wave",
}


GIF_POOL_MIN = 10
GIF_POOL_MAX = 30
GIF_MISS_TTL = 300
GIF_URL_TTL = 6 * 3600


def _is_valid_url(value) -> bool:
    """Validate a well-formed HTTP(S) URL."""
    if (
        not isinstance(value, str)
        or len(value) > 2000
        or any(c.isspace() for c in value)
    ):
        return False

    try:
        parts = urlparse(value)
        return parts.scheme in ("http", "https") and bool(parts.hostname)
    except ValueError:
        return False


def _display_name(user) -> str:
    return str(
        getattr(user, "display_name", None)
        or getattr(user, "name", None)
        or getattr(user, "id", "Someone")
    )


def _minecraft_embed(spec, text: str, *, user, count: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"{spec.emoji} {spec.title}",
        description=text,
        colour=discord.Colour(spec.color),
        timestamp=discord.utils.utcnow(),
    )
    times = "time" if count == 1 else "times"
    embed.set_footer(
        text=(
            f"Junior Atlas • {spec.category} • "
            f"{_display_name(user)} used this {count} {times}"
        )
    )
    return embed


class ActionView(SafeView):
    """Reciprocation button restricted to the original target."""

    def __init__(
        self,
        cog,
        action: str,
        initiator: discord.Member,
        target: discord.Member,
    ):
        super().__init__(timeout=180)
        self.cog = cog
        self.action = action
        self.initiator = initiator
        self.target = target
        self.used = False

        spec = get_action(action)
        emoji = spec.emoji if spec else SAFE_ACTIONS[action][1]
        label = spec.button_label if spec else f"{action.capitalize()} back!"

        self.reciprocate_button = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.primary,
            emoji=emoji,
        )
        self.reciprocate_button.callback = self.reciprocate_callback
        self.add_item(self.reciprocate_button)

    async def reciprocate_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.target.id:
            await safe_send(
                interaction,
                content=f"Only {self.target.mention} can use this button!",
                ephemeral=True,
            )
            return

        if self.used:
            await safe_send(
                interaction,
                content="That reciprocation has already been used.",
                ephemeral=True,
            )
            return

        self.used = True
        self.reciprocate_button.disabled = True

        try:
            if not await safe_edit(interaction, view=self):
                self.used = False
                self.reciprocate_button.disabled = False
                return

            await self.cog._execute_action(
                ctx_or_interaction=interaction,
                action=self.action,
                target=self.initiator,
                is_reciprocal=True,
            )
        except Exception:
            log.exception(
                "Reciprocal %r failed (initiator=%s, target=%s)",
                self.action,
                self.initiator.id,
                self.target.id,
            )
            self.used = False
            self.reciprocate_button.disabled = False
            await safe_edit(interaction, view=self)
            await safe_send(
                interaction,
                content="Something went wrong sending that. Please try again.",
                ephemeral=True,
            )
            return

        self.stop()


class ConsentView(discord.ui.View):
    """Accept / Decline prompt with reaction GIF integration."""

    def __init__(self, cog, initiator: discord.Member, target: discord.Member):
        super().__init__(timeout=120)
        self.cog = cog
        self.initiator = initiator
        self.target = target
        self.message: discord.Message | None = None

    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(
                f"Only {self.target.mention} can answer this!", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._disable_all()

        gif_url = await self.cog._get_reaction_url("fuck")
        if not gif_url:
            gif_url = await self.cog._get_reaction_url("kiss")

        embed = info_embed(
            "🔞 Fuck",
            f"{self.target.mention} accepted! {self.initiator.mention} fucked {self.target.mention}!",
        )
        if gif_url:
            embed.set_image(url=gif_url)

        embed.set_footer(text="Junior Atlas • Fun & community")
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="✖️")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._disable_all()
        embed = info_embed("🔞 Fuck", f"{self.target.mention} declined.")
        embed.set_footer(text="Junior Atlas • Fun & community")
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        log.error("ConsentView error", exc_info=error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
        except discord.HTTPException:
            pass

    async def on_timeout(self):
        self._disable_all()
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._counts: dict[tuple[int, int, str], int] = {}
        self._gif_pool: dict[str, dict[str, float]] = {}
        self._gif_miss: dict[str, float] = {}

        cog_commands = list(getattr(self, "__cog_commands__", []))

        # Dynamically register prefix commands for every standard action.
        for action_name in SAFE_ACTIONS:
            if action_name == "fuck":
                continue

            def make_callback(action):
                async def dynamic_command(
                    self_cog,
                    ctx,
                    member: discord.Member | None = None,
                ):
                    await self_cog._handle_cmd(ctx, action, member)

                return dynamic_command

            spec = get_action(action_name)
            description = (
                spec.description
                if spec
                else f"Playfully {action_name} someone"
            )
            callback = make_callback(action_name)
            callback.__name__ = action_name
            callback.__doc__ = description
            command_kwargs = {
                "name": action_name,
                "description": description,
                "help": description,
            }
            if spec is not None:
                command_kwargs["extras"] = action_extras(spec)
            prefix_cmd = commands.command(**command_kwargs)(callback)
            cog_commands.append(prefix_cmd)

        self.__cog_commands__ = cog_commands

    def _resolve_target(
        self,
        ctx_or_interaction: commands.Context | discord.Interaction,
        member: discord.Member | None,
    ) -> discord.Member | None:
        if member:
            return member

        # Handle both Context and test mocks that have the required attributes
        message = getattr(ctx_or_interaction, "message", None)
        if message and message.reference:
            resolved_msg = message.reference.resolved
            if isinstance(resolved_msg, discord.Message):
                author = resolved_msg.author
                if isinstance(author, discord.Member):
                    return author
                guild = getattr(ctx_or_interaction, "guild", None)
                return guild.get_member(author.id) if guild else None

        return None

    async def _get_reaction_url(self, key: str) -> str | None:
        if not key or not hasattr(self.bot, "reactions"):
            return None

        miss_until = self._gif_miss.get(key)
        if miss_until and time.monotonic() < miss_until:
            return None

        pool = self._gif_pool.setdefault(key, {})
        now = time.monotonic()
        stale_urls = [url for url, seen in pool.items() if now - seen > GIF_URL_TTL]
        for url in stale_urls:
            del pool[url]

        if len(pool) >= GIF_POOL_MIN and (len(pool) >= GIF_POOL_MAX or random.random() > 0.2):
            return random.choice(list(pool))

        try:
            result = self.bot.reactions.get(key)
            result = await result if inspect.isawaitable(result) else result
        except Exception:
            log.warning("Reaction provider failed for key %r", key, exc_info=True)
            self._gif_miss[key] = time.monotonic() + GIF_MISS_TTL
            return None

        if _is_valid_url(result):
            self._gif_miss.pop(key, None)
            if result in pool or len(pool) < GIF_POOL_MAX:
                pool[result] = time.monotonic()
            return result

        self._gif_miss[key] = time.monotonic() + GIF_MISS_TTL
        return None

    async def _bump_count(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        delta: int = 1,
    ) -> tuple[int, bool]:
        redis = getattr(self.bot, "cache", None)
        if redis is not None:
            try:
                result = redis.hincrby(
                    f"fun:counts:{guild_id}:{user_id}",
                    action,
                    delta,
                )
                result = await result if inspect.isawaitable(result) else result
                return int(result), True
            except Exception:
                log.exception(
                    "Redis counter update failed; refusing to split counter storage"
                )
                raise
        key = (guild_id, user_id, action)
        self._counts[key] = max(0, self._counts.get(key, 0) + delta)
        return self._counts[key], False

    async def _rollback_count(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        used_redis: bool,
    ) -> None:
        if used_redis:
            redis = getattr(self.bot, "cache", None)
            if redis is None:
                log.error("Cannot roll back Redis counter: Redis unavailable")
                return
            try:
                result = redis.hincrby(f"fun:counts:{guild_id}:{user_id}", action, -1)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                log.exception("Redis counter rollback failed")
            return

        key = (guild_id, user_id, action)
        self._counts[key] = max(0, self._counts.get(key, 0) - 1)

    def _local_art(self, action: str, spec) -> tuple[discord.File | None, str | None]:
        """Render original pixel art locally; never require an external host."""
        title = spec.title if spec else action.title()
        color = spec.color if spec else 0x5865F2
        category = spec.category if spec else "Fun"
        try:
            data = pixel_art.render_action_card(action, title, color, category)
        except Exception:
            log.debug("pixel-art fallback failed action=%s", action, exc_info=True)
            return None, None
        if not data:
            return None, None
        filename = f"junior-atlas-{action}.png"
        try:
            return discord.File(io.BytesIO(data), filename=filename), filename
        except Exception:
            log.debug("pixel-art attachment failed action=%s", action, exc_info=True)
            return None, None

    async def _award_interaction_xp(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        *,
        is_reciprocal: bool,
        self_target: bool,
    ):
        service = getattr(self.bot, "interaction_xp", None)
        if service is None or guild_id <= 0:
            return None
        try:
            return await service.award(
                guild_id,
                user_id,
                action,
                reciprocal=is_reciprocal,
                self_target=self_target,
            )
        except Exception:
            log.exception(
                "Friendship XP award failed guild=%s user=%s action=%s",
                guild_id,
                user_id,
                action,
            )
            return None

    @staticmethod
    def _apply_xp(embed: discord.Embed, result) -> None:
        if result.awarded:
            line = f"**+{result.amount} Friendship XP!**"
            if result.level_up:
                line += (
                    f"\n**Level up!** You reached Friendship Level "
                    f"{result.level} — {FriendshipXP.level_title(result.level)}."
                )
        else:
            remaining = math.ceil(max(0.0, result.cooldown_remaining))
            line = (
                f"*Friendship XP is cooling down — ready in {remaining}s.*"
                if remaining > 0
                else "*Friendship XP is ready again.*"
            )
        description = embed.description or ""
        embed.description = f"{description}\n\n{line}"
        embed.add_field(
            name="Friendship Level",
            value=(
                f"Level {result.level} • "
                f"{result.level_xp}/{result.next_level_xp} XP"
            ),
            inline=True,
        )

    async def _execute_action(
        self,
        ctx_or_interaction: commands.Context | discord.Interaction,
        action: str,
        target: discord.Member | None,
        is_reciprocal: bool = False,
    ):
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)

        user = (
            ctx_or_interaction.user
            if is_interaction
            else ctx_or_interaction.author
        )

        target_member = target or user
        spec = get_action(action)
        action_data = SAFE_ACTIONS[action]

        if spec is not None:
            key = spec.gif_key
            emoji = spec.emoji
            initial_verb = spec.initial_verb
            reciprocate_verb = spec.reciprocate_verb
        else:
            key, emoji, initial_verb, reciprocate_verb = action_data

        url = None
        if spec is None or spec.uses_gif:
            url = await self._get_reaction_url(key)
            if not url:
                fallback_key = GIF_FALLBACKS.get(key, "")
                if fallback_key:
                    url = await self._get_reaction_url(fallback_key)

        attachment = None
        attachment_name = None
        if not url:
            attachment, attachment_name = self._local_art(action, spec)

        if target_member.id == user.id:
            if spec is not None:
                text = random.choice(spec.self_responses)
            else:
                text = (
                    f"{user.mention} {initial_verb} themselves!\n"
                    "*Tip: mention someone or reply to their message to target them.*"
                )
            view = None
        elif is_reciprocal:
            if spec is not None:
                text = random.choice(
                    spec.reciprocal_responses or spec.responses
                )
            else:
                text = (
                    f"{user.mention} {reciprocate_verb} "
                    f"{target_member.mention}!"
                )
            view = None
        else:
            if spec is not None:
                text = random.choice(spec.responses)
            else:
                text = (
                    f"{user.mention} {initial_verb} "
                    f"{target_member.mention}!"
                )
            view = ActionView(self, action, user, target_member)

        text = text.format(
            actor=user.mention,
            target=target_member.mention,
        )

        guild = getattr(ctx_or_interaction, "guild", None)
        guild_id = guild.id if guild else 0

        count, used_redis = await self._bump_count(
            guild_id,
            user.id,
            action,
        )

        if spec is not None:
            embed = _minecraft_embed(spec, text, user=user, count=count)
        else:
            embed = info_embed(f"{emoji} {action.title()}", text)
            embed.set_footer(
                text=(
                    f"{_display_name(user)} has used {action} "
                    f"{count} time{'s' if count != 1 else ''} "
                    "• Junior Atlas"
                )
            )

        if url:
            embed.set_image(url=url)
        elif attachment_name:
            embed.set_image(url=f"attachment://{attachment_name}")

        kwargs = {"embed": embed}

        if view is not None:
            kwargs["view"] = view
        if attachment is not None:
            kwargs["file"] = attachment

        message = None
        delivered = False

        try:
            if is_interaction:
                if not ctx_or_interaction.response.is_done():
                    await safe_defer(ctx_or_interaction, ephemeral=False)

                message = await ctx_or_interaction.followup.send(
                    wait=True,
                    **kwargs,
                )
                delivered = True
            else:
                message = await ctx_or_interaction.send(**kwargs)
                delivered = True

        except Exception:
            if not delivered:
                await self._rollback_count(
                    guild_id,
                    user.id,
                    action,
                    used_redis,
                )

            raise

        if view is not None and message is not None:
            view.message = message

        xp_result = await self._award_interaction_xp(
            guild_id,
            user.id,
            action,
            is_reciprocal=is_reciprocal,
            self_target=target_member.id == user.id,
        )
        if xp_result is not None:
            self._apply_xp(embed, xp_result)
            if message is not None:
                try:
                    await message.edit(embed=embed)
                except Exception:
                    log.debug(
                        "Could not update interaction embed with XP guild=%s action=%s",
                        guild_id,
                        action,
                        exc_info=True,
                    )

    @staticmethod
    async def _ephemeral_reply(ctx_or_interaction, text: str) -> None:
        """Reply privately to either a prefix context or a slash interaction."""
        if isinstance(ctx_or_interaction, discord.Interaction):
            await safe_send(ctx_or_interaction, content=text, ephemeral=True)
            return
        await ctx_or_interaction.send(text, ephemeral=True)

    async def _handle_cmd(
        self,
        ctx_or_interaction: commands.Context | discord.Interaction,
        action: str,
        member: discord.Member | None = None,
    ):
        if action not in SAFE_ACTIONS:
            await self._ephemeral_reply(
                ctx_or_interaction,
                f"Unknown action `{action}`. Use `/action` to choose a valid action.",
            )
            return

        ctx = ctx_or_interaction
        guild_marker = getattr(ctx, "guild", object())
        if guild_marker is None:
            await self._ephemeral_reply(
                ctx, "These interactions only work in servers."
            )
            return

        target = self._resolve_target(ctx, member)
        message = getattr(ctx, "message", None)
        replied = bool(message and getattr(message, "reference", None))

        if member is None and replied and target is None:
            await self._ephemeral_reply(
                ctx, "I couldn't find that person in this server."
            )
            return

        if (
            target is not None
            and isinstance(target, discord.Member)
            and hasattr(guild_marker, "id")
            and target.guild.id != guild_marker.id
        ):
            await self._ephemeral_reply(
                ctx, "I couldn't find that person in this server."
            )
            return

        if target is not None and getattr(target, "bot", False):
            await self._ephemeral_reply(
                ctx,
                f"You can't {action} a bot! Try a fellow adventurer.",
            )
            return

        await self._execute_action(ctx, action, target)

    @commands.hybrid_command(
        name="friendship",
        description="Show Friendship XP and interaction statistics",
        help="Show your Friendship XP, level and most-used interactions.",
        extras={
            "help_category": "Minecraft",
            "usage_prefix": "<prefix>friendship [member]",
            "usage_slash": "/friendship [member]",
            "example_prefix": ",friendship @member",
            "example_slash": "/friendship member:@member",
            "cooldown": "No command cooldown; XP awards share a "
            f"{XP_COOLDOWN_SECONDS}s cooldown",
            "permissions": "Send Messages; Embed Links (bot)",
        },
    )
    @commands.guild_only()
    @app_commands.describe(member="Member to inspect (defaults to you)")
    async def friendship(
        self,
        ctx: commands.Context,
        member: discord.Member | None = None,
    ):
        target = member or ctx.author
        service = getattr(self.bot, "interaction_xp", None)
        if service is None:
            await ctx.send(
                embed=error_embed(
                    "Friendship unavailable",
                    "Friendship XP is not available right now.",
                ),
                ephemeral=True,
            )
            return

        try:
            stats = await service.stats(ctx.guild.id, target.id)
        except Exception:
            log.exception(
                "Friendship stats failed guild=%s user=%s",
                getattr(ctx.guild, "id", None),
                getattr(target, "id", None),
            )
            await ctx.send(
                embed=error_embed(
                    "Friendship unavailable",
                    "I couldn't load that Friendship record. Please try again.",
                ),
                ephemeral=True,
            )
            return

        if stats is None:
            await ctx.send(
                embed=info_embed(
                    f"💚 Friendship • {_display_name(target)}",
                    f"{target.mention} has no recorded interactions yet.\n"
                    "Try `/hug`, `/mine`, `/craft`, or `/friendship` after your "
                    "first adventure!",
                ),
                ephemeral=True,
            )
            return

        embed = info_embed(
            f"💚 Friendship • {_display_name(target)}",
            f"{target.mention} has **{stats.total_xp:,} Friendship XP**.",
        )
        embed.add_field(
            name="Level",
            value=(
                f"**{stats.level}** • "
                f"{FriendshipXP.level_title(stats.level)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Progress",
            value=f"{stats.level_xp}/{stats.next_level_xp} XP",
            inline=True,
        )
        embed.add_field(
            name="Interactions",
            value=f"{stats.interactions:,}",
            inline=True,
        )
        embed.add_field(
            name="Reciprocations",
            value=f"{stats.reciprocations:,}",
            inline=True,
        )
        embed.add_field(
            name="XP Cooldown",
            value=(
                "Ready now"
                if stats.cooldown_remaining <= 0
                else f"Ready in {math.ceil(stats.cooldown_remaining)}s"
            ),
            inline=True,
        )
        top_actions = service.top_actions(stats.action_counts)
        embed.add_field(
            name="Most-used interactions",
            value=(
                "\n".join(
                    f"{action_emoji(name)} **{name}** — {count:,}"
                    for name, count in top_actions
                )
                if top_actions
                else "No interactions recorded yet."
            ),
            inline=False,
        )
        embed.set_footer(text="Junior Atlas • Friendship XP")
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="fuck", description="NSFW channels only - the other person must accept")
    @commands.guild_only()
    @commands.is_nsfw()
    async def fuck(self, ctx: commands.Context, member: discord.Member | None = None):
        target = self._resolve_target(ctx, member)
        if (
            target is None
            or not isinstance(target, discord.Member)
            or target.guild.id != ctx.guild.id
            or target.id == ctx.author.id
            or target.bot
        ):
            await ctx.send("Mention someone else (or reply to their message)!", ephemeral=True)
            return

        view = ConsentView(self, ctx.author, target)
        embed = info_embed(
            "🔞 Fuck",
            f"{ctx.author.mention} wants to fuck {target.mention}.\n"
            f"{target.mention}, do you accept?",
        )
        embed.set_footer(text="Junior Atlas • Fun & community")
        view.message = await ctx.send(
            content=target.mention,
            embed=embed,
            view=view,
            allowed_mentions=discord.AllowedMentions(users=[target]),
        )

    @fuck.error
    async def fuck_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NSFWChannelRequired):
            await ctx.send("This command only works in age-restricted (NSFW) channels.", ephemeral=True)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command only works in servers.", ephemeral=True)
        else:
            raise error


# The Minecraft catalogue keeps dedicated top-level slash commands.  Legacy
# actions remain reachable through the single ``/action`` selector so the
# application stays below Discord's 100-root-command limit.
PRIMARY_SLASH_ACTIONS = ACTION_ORDER
SECONDARY_SLASH_ACTIONS = tuple(
    action for action in SAFE_ACTIONS if action != "fuck"
)

# Discord rejects an option that declares more than 25 static choices.  The
# ``/action`` command exposes every secondary action through autocomplete so the
# full catalogue remains available without exceeding that limit.
ACTION_CHOICE_LIMIT = 25


def _action_description(action: str) -> str:
    """Return a short human-readable description for an action."""
    spec = get_action(action)
    if spec is not None:
        return spec.description
    _key, _emoji, initial_verb = SAFE_ACTIONS[action][:3]
    return f"{initial_verb} someone"


def action_choices(
    current: str = "",
    *,
    limit: int = ACTION_CHOICE_LIMIT,
) -> list[discord.app_commands.Choice[str]]:
    """Return autocomplete choices matching ``current``.

    Matching is case-insensitive and considers both the action name and its
    description.  Exact and prefix matches are ranked ahead of substring
    matches, and the result is always capped at Discord's 25-choice limit.
    """
    query = (current or "").strip().casefold()
    ranked: list[tuple[int, str]] = []

    for action in SECONDARY_SLASH_ACTIONS:
        description = _action_description(action)
        action_folded = action.casefold()
        if query and query not in action_folded and query not in description.casefold():
            continue

        if not query or action_folded == query:
            rank = 0
        elif action_folded.startswith(query):
            rank = 1
        elif query in action_folded:
            rank = 2
        else:
            rank = 3
        ranked.append((rank, action))

    ranked.sort(key=lambda item: (item[0], item[1]))
    capped_limit = max(0, min(limit, ACTION_CHOICE_LIMIT))
    return [
        discord.app_commands.Choice(
            name=f"{action.title()} — {_action_description(action)}",
            value=action,
        )
        for _rank, action in ranked[:capped_limit]
    ]


async def action_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice[str]]:
    """Discord autocomplete handler for the ``/action`` selector."""
    return action_choices(current)


def make_action_slash_callback(cog, action):
    # The first parameter is the interaction and is never exposed as an option.
    # ``member`` stays optional so both ``/hug`` and ``/hug member:@user`` work.
    async def slash_callback(
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ):
        await cog._handle_cmd(interaction, action, member)

    slash_callback.__name__ = action
    slash_callback = discord.app_commands.describe(
        member="Member to target (defaults to you)"
    )(slash_callback)
    slash_callback = discord.app_commands.guild_only()(slash_callback)
    return slash_callback


def make_action_selector_callback(cog):
    async def action_callback(
        interaction: discord.Interaction,
        action: str,
        member: discord.Member | None = None,
    ):
        if action not in SECONDARY_SLASH_ACTIONS:
            await cog._ephemeral_reply(
                interaction,
                f"Unknown action `{action}`. Choose one of the suggestions from `/action`.",
            )
            return
        await cog._handle_cmd(interaction, action, member)

    action_callback.__name__ = "action"
    action_callback = discord.app_commands.describe(
        action="Social action to perform (type to search)",
        member="Member to target (defaults to you or the replied-to message)",
    )(action_callback)
    action_callback = discord.app_commands.autocomplete(
        action=action_autocomplete
    )(action_callback)
    action_callback = discord.app_commands.guild_only()(action_callback)
    return action_callback


async def setup(bot):
    await bot.add_cog(Fun(bot))
    cog = bot.get_cog("Fun")
    for action_name in PRIMARY_SLASH_ACTIONS:
        spec = get_action(action_name)
        slash_callback = make_action_slash_callback(cog, action_name)
        slash_command = discord.app_commands.Command(
            name=action_name,
            description=spec.description if spec else f"Playfully {action_name} someone",
            callback=slash_callback,
            extras=action_extras(spec) if spec else None,
        )
        bot.tree.add_command(slash_command)

    # One extra command exposes every remaining legacy action without
    # exceeding Discord's per-application command limit.
    action_callback = make_action_selector_callback(cog)
    bot.tree.add_command(
        discord.app_commands.Command(
            name="action",
            description="Choose any social, Minecraft, or playful interaction",
            callback=action_callback,
            extras={
                "help_category": "Fun",
                "usage_prefix": "<prefix>action <action> [member]",
                "usage_slash": "/action <action> [member]",
                "example_prefix": ",action mine @member",
                "example_slash": "/action action:mine member:@member",
                "cooldown": f"{XP_COOLDOWN_SECONDS}s Friendship XP cooldown",
                "permissions": "Send Messages; Embed Links (bot)",
            },
        )
    )

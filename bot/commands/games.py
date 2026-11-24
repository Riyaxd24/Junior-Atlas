"""Interactive UNO and Hand Cricket commands.

Games are played entirely through Discord UI components. The rules engines
validate every move, so a stale/forged interaction cannot bypass turn order.
Active engine state is persisted to Redis where available and can be resumed
after a restart with the ``resume`` option.
"""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from bot.services.game_sessions import GameStore
from bot.services.games import (
    UNO_COLORS,
    HandCricketEngine,
    UnoEngine,
)
from bot.ui import error_embed, info_embed, success_embed, warning_embed

log = logging.getLogger(__name__)

UNO_KIND = "uno"
CRICKET_KIND = "handcricket"


def _player_map(guild, player_ids):
    result = {}
    for player_id in player_ids:
        member = guild.get_member(player_id) if guild else None
        result[player_id] = member
    return result


def _mention(player_id, members):
    member = members.get(player_id)
    return member.mention if member is not None else f"<@{player_id}>"


class UnoLobbyView(discord.ui.View):
    def __init__(self, bot, host, store):
        super().__init__(timeout=180)
        self.bot = bot
        self.host = host
        self.store = store
        self.players = [host]
        self.message: discord.Message | None = None
        self.start_button.disabled = True

    @property
    def guild_id(self):
        return self.host.guild.id

    @property
    def channel_id(self):
        return self.message.channel.id if self.message is not None else 0

    def _embed(self):
        names = "\n".join(f"• {member.mention}" for member in self.players)
        embed = info_embed(
            "🎴 UNO — Lobby",
            f"Host: {self.host.mention}\n\n**Players ({len(self.players)}/6)**\n{names}\n\n"
            "Press **Join** to enter, then the host starts the game.",
        )
        embed.set_footer(text="2–6 players · 7 cards each · 3 minute lobby timeout")
        return embed

    async def _refresh(self, interaction):
        self.start_button.disabled = len(self.players) < 2
        await interaction.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success, emoji="➕")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("You already joined.", ephemeral=True)
            return
        if len(self.players) >= UnoEngine.MAX_PLAYERS:
            await interaction.response.send_message("This lobby is full.", ephemeral=True)
            return
        self.players.append(interaction.user)
        await self._refresh(interaction)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, emoji="➖")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            await interaction.response.send_message("You are not in this lobby.", ephemeral=True)
            return
        if interaction.user.id == self.host.id:
            await interaction.response.send_message(
                "The host cannot leave. Press **Cancel** to close the lobby.", ephemeral=True
            )
            return
        self.players.remove(interaction.user)
        await self._refresh(interaction)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, emoji="▶️")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host.id:
            await interaction.response.send_message("Only the host can start.", ephemeral=True)
            return
        if len(self.players) < 2:
            await interaction.response.send_message("At least two players are needed.", ephemeral=True)
            return
        engine = UnoEngine([member.id for member in self.players]).start()
        view = UnoGameView(
            self.bot,
            engine,
            {member.id: member for member in self.players},
            self.store,
            self.guild_id,
            self.channel_id or interaction.channel.id,
        )
        await self.store.save(self.guild_id, self.channel_id or interaction.channel.id, UNO_KIND, engine)
        self.stop()
        await interaction.response.edit_message(embed=view.make_embed(), view=view)
        try:
            view.message = await interaction.original_response()
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host.id:
            await interaction.response.send_message("Only the host can cancel.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        self.stop()
        await interaction.response.edit_message(
            embed=warning_embed("UNO lobby closed", "The host cancelled this lobby."),
            view=self,
        )

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


class UnoGameView(discord.ui.View):
    def __init__(self, bot, engine, members, store, guild_id, channel_id):
        super().__init__(timeout=600)
        self.bot = bot
        self.engine = engine
        self.members = members
        self.store = store
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.selected_color = None
        self.message: discord.Message | None = None
        self._build_controls()

    def _build_controls(self):
        self.card_select = discord.ui.Select(placeholder="Play a card", row=0, min_values=1, max_values=1)
        self.card_select.callback = self._on_card
        self.add_item(self.card_select)

        self.color_select = discord.ui.Select(
            placeholder="Choose a colour for a wild card",
            row=1,
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=color.title(), value=color) for color in UNO_COLORS],
        )
        self.color_select.callback = self._on_color
        self.add_item(self.color_select)

        self.draw_button = discord.ui.Button(
            label="Draw a card", style=discord.ButtonStyle.secondary, emoji="🃏", row=2
        )
        self.draw_button.callback = self._on_draw
        self.add_item(self.draw_button)

        self.rematch_button = discord.ui.Button(
            label="Rematch", style=discord.ButtonStyle.success, emoji="🔁", row=2
        )
        self.rematch_button.callback = self._on_rematch
        self.rematch_button.disabled = True
        self.add_item(self.rematch_button)
        self._sync()

    def _sync(self):
        current = self.engine.current_player()
        hand = self.engine.hand(current)
        indexed = list(enumerate(hand))
        # Playable cards first so they are always inside Discord's 25-option cap.
        indexed.sort(key=lambda item: 0 if self.engine.can_play(item[1]) else 1)
        self.card_select.options = [
            discord.SelectOption(
                label=card.label,
                value=str(index),
                description="Playable now" if self.engine.can_play(card) else None,
            )
            for index, card in indexed[:25]
        ] or [discord.SelectOption(label="No cards", value="none")]
        game_over = self.engine.winner_id is not None
        self.card_select.disabled = game_over
        self.color_select.disabled = game_over
        self.draw_button.disabled = game_over
        self.rematch_button.disabled = not game_over

    def make_embed(self):
        current = self.engine.current_player()
        embed = info_embed(
            "🎴 UNO",
            f"**Discard:** {self.engine.top.label}\n"
            f"**Current colour:** {self.engine.current_color.title() if self.engine.current_color else '—'}\n"
            f"**Turn:** {_mention(current, self.members)}",
        )
        counts = "\n".join(
            f"• {_mention(player_id, self.members)} — **{len(self.engine.hand(player_id))}** cards"
            for player_id in self.engine.player_ids
        )
        embed.add_field(name="Players", value=counts, inline=False)
        if self.engine.winner_id is not None:
            if self.engine.winner_id == 0:
                embed.description = "The game ended in a draw."
            else:
                embed.description = f"🏆 {_mention(self.engine.winner_id, self.members)} wins!"
        embed.set_footer(text="Select a card to play · choose a colour before a wild card · Draw ends your turn")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.engine.player_ids:
            await interaction.response.send_message("You are not part of this game.", ephemeral=True)
            return False
        return True

    async def _replace(self, interaction):
        self._sync()
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def _on_color(self, interaction: discord.Interaction):
        self.selected_color = self.color_select.values[0]
        await interaction.response.send_message(
            f"Wild colour set to **{self.selected_color.title()}**. Now play your wild card.",
            ephemeral=True,
        )

    async def _on_card(self, interaction: discord.Interaction):
        if self.card_select.values[0] == "none":
            await interaction.response.send_message("You have no cards to play.", ephemeral=True)
            return
        card = self.engine.hand(self.engine.current_player())[int(self.card_select.values[0])]
        chosen = self.selected_color if card.color == "wild" else None
        try:
            result = self.engine.play(interaction.user.id, int(self.card_select.values[0]), chosen)
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        self.selected_color = None
        await self.store.save(self.guild_id, self.channel_id, UNO_KIND, self.engine)
        if self.engine.winner_id is not None:
            await self.store.clear(self.guild_id, self.channel_id, UNO_KIND)
        await self._replace(interaction)

    async def _on_draw(self, interaction: discord.Interaction):
        try:
            self.engine.draw(interaction.user.id)
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await self.store.save(self.guild_id, self.channel_id, UNO_KIND, self.engine)
        await self._replace(interaction)

    async def _on_rematch(self, interaction: discord.Interaction):
        if interaction.user.id not in self.engine.player_ids:
            await interaction.response.send_message("Only players can start a rematch.", ephemeral=True)
            return
        self.engine = UnoEngine(list(self.engine.player_ids)).start()
        self.selected_color = None
        await self.store.save(self.guild_id, self.channel_id, UNO_KIND, self.engine)
        await self._replace(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


class HandCricketView(discord.ui.View):
    def __init__(self, bot, engine, members, store, guild_id, channel_id):
        super().__init__(timeout=900)
        self.bot = bot
        self.engine = engine
        self.members = members
        self.store = store
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message: discord.Message | None = None
        for number in range(1, 7):
            button = discord.ui.Button(
                label=str(number),
                style=discord.ButtonStyle.primary,
                row=0 if number <= 3 else 1,
                custom_id=f"hc:{number}",
            )
            button.callback = self._make_choice(number)
            self.add_item(button)
        self.rematch_button = discord.ui.Button(
            label="Rematch", style=discord.ButtonStyle.success, emoji="🔁", row=2
        )
        self.rematch_button.callback = self._on_rematch
        self.rematch_button.disabled = True
        self.add_item(self.rematch_button)

    def make_embed(self):
        engine = self.engine
        striker = _mention(engine.striker_id, self.members)
        bowler = _mention(engine.bowler_id, self.members)
        embed = info_embed(
            "🏏 Hand Cricket",
            f"**Innings {engine.innings}** · {engine.overs} over(s)\n"
            f"**Striker:** {striker}\n**Bowler:** {bowler}\n"
            f"**Balls left:** {engine.balls_left}",
        )
        embed.add_field(
            name="Score",
            value=(
                f"{_mention(engine.player_ids[0], self.members)} — "
                f"**{engine.scores[engine.player_ids[0]]}**\n"
                f"{_mention(engine.player_ids[1], self.members)} — "
                f"**{engine.scores[engine.player_ids[1]]}**"
            ),
            inline=True,
        )
        if engine.target is not None:
            embed.add_field(name="Target", value=str(engine.target), inline=True)
        if engine.game_over:
            if engine.winner_id == 0:
                embed.description = "The match is tied!"
            else:
                embed.description = f"🏆 {_mention(engine.winner_id, self.members)} wins the match!"
        embed.set_footer(text="Both players pick 1–6 secretly. Equal numbers means OUT.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.engine.player_ids:
            await interaction.response.send_message("You are not part of this match.", ephemeral=True)
            return False
        return True

    def _make_choice(self, number):
        async def callback(interaction: discord.Interaction):
            try:
                result = self.engine.submit(interaction.user.id, number)
            except ValueError as error:
                await interaction.response.send_message(str(error), ephemeral=True)
                return
            if not result.ball_complete:
                await interaction.response.send_message(
                    f"You chose **{number}**. " + result.message, ephemeral=True
                )
                return
            await self.store.save(self.guild_id, self.channel_id, CRICKET_KIND, self.engine)
            if self.engine.game_over:
                await self.store.clear(self.guild_id, self.channel_id, CRICKET_KIND)
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id != "hc:rematch":
                    child.disabled = self.engine.game_over
            self.rematch_button.disabled = not self.engine.game_over
            await interaction.response.edit_message(embed=self.make_embed(), view=self)

        return callback

    async def _on_rematch(self, interaction: discord.Interaction):
        if interaction.user.id not in self.engine.player_ids:
            await interaction.response.send_message("Only players can start a rematch.", ephemeral=True)
            return
        self.engine = HandCricketEngine(
            self.engine.player_ids[0], self.engine.player_ids[1], overs=self.engine.overs
        )
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = child.custom_id == "hc:rematch"
        await self.store.save(self.guild_id, self.channel_id, CRICKET_KIND, self.engine)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.store = GameStore(getattr(bot, "cache", None))

    @commands.hybrid_command(name="uno", description="Start an interactive UNO game")
    @commands.guild_only()
    async def uno(self, ctx: commands.Context, resume: bool = False):
        guild, channel = ctx.guild, ctx.channel
        if resume:
            engine = await self.store.load_engine(
                guild.id, channel.id, UNO_KIND, UnoEngine.from_dict
            )
            if engine is None:
                await ctx.send(embed=error_embed("No saved game", "There is no UNO game to resume in this channel."))
                return
            view = UnoGameView(
                self.bot,
                engine,
                _player_map(guild, engine.player_ids),
                self.store,
                guild.id,
                channel.id,
            )
            message = await ctx.send(embed=view.make_embed(), view=view)
            view.message = message
            return
        existing = await self.store.load_engine(guild.id, channel.id, UNO_KIND, UnoEngine.from_dict)
        if existing is not None:
            await ctx.send(
                embed=error_embed(
                    "Game already in progress",
                    "Use `/uno resume:true` to continue the saved game or finish it first.",
                )
            )
            return
        view = UnoLobbyView(self.bot, ctx.author, self.store)
        message = await ctx.send(embed=view._embed(), view=view)
        view.message = message

    @commands.hybrid_command(
        name="handcricket",
        aliases=["hc"],
        description="Play Hand Cricket against another member",
    )
    @commands.guild_only()
    async def handcricket(
        self,
        ctx: commands.Context,
        opponent: discord.Member = None,
        overs: int = 1,
        resume: bool = False,
    ):
        guild, channel = ctx.guild, ctx.channel
        if resume:
            engine = await self.store.load_engine(
                guild.id, channel.id, CRICKET_KIND, HandCricketEngine.from_dict
            )
            if engine is None:
                await ctx.send(embed=error_embed("No saved match", "There is no Hand Cricket match to resume in this channel."))
                return
            view = HandCricketView(
                self.bot,
                engine,
                _player_map(guild, engine.player_ids),
                self.store,
                guild.id,
                channel.id,
            )
            message = await ctx.send(embed=view.make_embed(), view=view)
            view.message = message
            return
        if opponent is None:
            await ctx.send(embed=error_embed("Opponent required", "Mention the member you want to play against."))
            return
        if opponent.bot or opponent.id == ctx.author.id:
            await ctx.send(embed=error_embed("Invalid opponent", "Choose another human member."))
            return
        if not 1 <= int(overs) <= 50:
            await ctx.send(embed=error_embed("Invalid overs", "Overs must be between 1 and 50."))
            return
        existing = await self.store.load_engine(
            guild.id, channel.id, CRICKET_KIND, HandCricketEngine.from_dict
        )
        if existing is not None:
            await ctx.send(
                embed=error_embed(
                    "Match already in progress",
                    "Use `/handcricket resume:true` to continue the saved match.",
                )
            )
            return
        engine = HandCricketEngine(ctx.author.id, opponent.id, overs=overs)
        view = HandCricketView(
            self.bot,
            engine,
            {ctx.author.id: ctx.author, opponent.id: opponent},
            self.store,
            guild.id,
            channel.id,
        )
        await self.store.save(guild.id, channel.id, CRICKET_KIND, engine)
        message = await ctx.send(embed=view.make_embed(), view=view)
        view.message = message


async def setup(bot):
    await bot.add_cog(Games(bot))

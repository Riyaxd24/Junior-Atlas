import random

import discord
from discord import app_commands
from discord.ext import commands

from bot.services.community import CommunityService
from bot.services.games import RPSEngine, TicTacToeEngine, TriviaEngine
from bot.ui import error_embed, info_embed, success_embed


class TicTacToeButton(discord.ui.Button):
    def __init__(self, row, column, view):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=row)
        self.game_row = row
        self.game_column = column
        self.game_view = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in (self.game_view.player_x.id, self.game_view.player_o.id):
            await interaction.response.send_message("You are not part of this game.", ephemeral=True)
            return
        if interaction.user.id != self.game_view.current_player.id:
            await interaction.response.send_message("It is not your turn.", ephemeral=True)
            return
        player = 1 if interaction.user.id == self.game_view.player_x.id else 2
        try:
            result = self.game_view.engine.move(self.game_row, self.game_column, player)
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        self.label = "X" if player == 1 else "O"
        self.disabled = True
        if result is not None:
            for child in self.game_view.children:
                child.disabled = True
            if result == 0:
                text = "The game ended in a draw."
            else:
                winner = self.game_view.player_x if result == 1 else self.game_view.player_o
                text = f"{winner.mention} wins!"
            self.game_view.stop()
            await interaction.response.edit_message(
                embed=info_embed("Tic-Tac-Toe — Game Over", text),
                view=self.game_view,
            )
            return
        self.game_view.current_player = (
            self.game_view.player_o
            if interaction.user.id == self.game_view.player_x.id
            else self.game_view.player_x
        )
        await interaction.response.edit_message(
            embed=info_embed(
                "Tic-Tac-Toe",
                f"Current turn: {self.game_view.current_player.mention}",
            ),
            view=self.game_view,
        )


class TicTacToeView(discord.ui.View):
    def __init__(self, player_x, player_o):
        super().__init__(timeout=120)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = player_x
        self.engine = TicTacToeEngine()
        for row in range(3):
            for column in range(3):
                self.add_item(TicTacToeButton(row, column, self))


class RPSView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=60)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}

    async def choose(self, interaction, choice):
        if interaction.user.id not in (self.player1.id, self.player2.id):
            await interaction.response.send_message(
                "You are not part of this match.",
                ephemeral=True,
            )
            return
        if interaction.user.id in self.choices:
            await interaction.response.send_message(
                "You already chose.",
                ephemeral=True,
            )
            return
        self.choices[interaction.user.id] = choice
        await interaction.response.send_message(
            f"You chose **{choice}**.",
            ephemeral=True,
        )
        if len(self.choices) == 2:
            winner = RPSEngine.winner(
                self.choices[self.player1.id],
                self.choices[self.player2.id],
            )
            if winner == 0:
                text = "It is a draw."
            elif winner == 1:
                text = f"{self.player1.mention} wins!"
            else:
                text = f"{self.player2.mention} wins!"
            self.stop()
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(
                embed=success_embed("Rock-Paper-Scissors", text),
                view=self,
            )

    @discord.ui.button(label="Rock", emoji="🪨")
    async def rock(self, interaction, button):
        await self.choose(interaction, "rock")

    @discord.ui.button(label="Paper", emoji="📄")
    async def paper(self, interaction, button):
        await self.choose(interaction, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️")
    async def scissors(self, interaction, button):
        await self.choose(interaction, "scissors")


class TriviaView(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=60)
        self.player = player
        self.engine = TriviaEngine()
        for option in self.engine.options:
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.secondary)
            button.callback = self.make_callback(option)
            self.add_item(button)

    def make_callback(self, option):
        async def callback(interaction):
            if interaction.user.id != self.player.id:
                await interaction.response.send_message(
                    "This trivia question is not for you.",
                    ephemeral=True,
                )
                return
            correct = self.engine.correct(option)
            self.stop()
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(
                embed=success_embed(
                    "Trivia",
                    f"{self.engine.question}\n\n"
                    + ("Correct!" if correct else f"The answer was **{self.engine.answer}**."),
                ),
                view=self,
            )

        return callback


class Engagement(commands.GroupCog, name='engage'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='poll', description='Create a simple poll')
    async def poll(self, interaction: discord.Interaction, question: str):
        if len(question) > 250:
            return await interaction.response.send_message(embed=error_embed('Poll too long', 'Keep the question under 250 characters.'), ephemeral=True)
        embed = info_embed('📊 Community Poll', question)
        embed.add_field(name='Vote', value='👍 Yes\n👎 No', inline=False)
        embed.set_footer(text=f'Created by {interaction.user.display_name}')
        message = await interaction.channel.send(embed=embed)
        for emoji in ('👍', '👎'):
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass
        await interaction.response.send_message(embed=success_embed('Poll created', f'Your poll is live in {interaction.channel.mention}.'), ephemeral=True)

    @app_commands.command(name='8ball', description='Ask the magic 8-ball')
    async def eightball(self, interaction: discord.Interaction, question: str):
        if not question.strip():
            return await interaction.response.send_message(embed=error_embed('Question required', 'Ask the 8-ball something first.'), ephemeral=True)
        answer = random.choice(('Yes.', 'No.', 'Maybe.', 'Ask again later.', 'Definitely.'))
        embed = info_embed('🎱 Magic 8-Ball', f'**Question:** {question[:500]}\n\n**Answer:** {answer}')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='choose', description='Choose between options separated by |')
    async def choose(self, interaction: discord.Interaction, options: str):
        vals = [x.strip() for x in options.split('|') if x.strip()]
        if len(vals) < 2:
            return await interaction.response.send_message(embed=error_embed('Not enough options', 'Give at least two options separated by `|`.'), ephemeral=True)
        if len(vals) > 20:
            return await interaction.response.send_message(embed=error_embed('Too many options', 'Keep the choice list to 20 options or fewer.'), ephemeral=True)
        selected = random.choice(vals)
        embed = success_embed('Choice made', f'🎯 I choose **{selected[:200]}**.')
        embed.add_field(name='Options', value=' • '.join(f'`{v[:80]}`' for v in vals), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='tictactoe', description='Play Tic-Tac-Toe')
    @app_commands.guild_only()
    async def tictactoe(
        self,
        interaction: discord.Interaction,
        opponent: discord.Member,
    ):
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "Choose another human opponent.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=info_embed(
                "Tic-Tac-Toe",
                f"{interaction.user.mention} (X) vs {opponent.mention} (O)",
            ),
            view=TicTacToeView(interaction.user, opponent),
        )

    @app_commands.command(name='rps', description='Play Rock-Paper-Scissors')
    @app_commands.guild_only()
    async def rps(
        self,
        interaction: discord.Interaction,
        opponent: discord.Member,
    ):
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "Choose another human opponent.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=info_embed(
                "Rock-Paper-Scissors",
                f"{interaction.user.mention} vs {opponent.mention}",
            ),
            view=RPSView(interaction.user, opponent),
        )

    @app_commands.command(name='trivia', description='Start a trivia quiz')
    @app_commands.guild_only()
    async def trivia(self, interaction: discord.Interaction):
        view = TriviaView(interaction.user)
        await interaction.response.send_message(
            embed=info_embed(
                "Trivia",
                view.engine.question,
            ),
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name='collect', description='Claim your daily community collectible')
    @app_commands.guild_only()
    async def collect(self, interaction: discord.Interaction):
        item = await CommunityService(self.bot.db, self.bot.cache).daily_collect(
            interaction.guild.id,
            interaction.user.id,
        )
        if item is None:
            await interaction.response.send_message(
                "Your daily collectible is already claimed.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=success_embed(
                "Daily collectible",
                f"You found **{item.emoji} {item.name}** ({item.rarity}).",
            )
        )

    @app_commands.command(name='tempvoice', description='Configure a join-to-create voice hub')
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    async def tempvoice(
        self,
        interaction: discord.Interaction,
        hub: discord.VoiceChannel,
        category: discord.CategoryChannel | None = None,
        name_format: str = "{user}'s Channel",
        user_limit: app_commands.Range[int, 0, 99] = 0,
    ):
        await CommunityService(self.bot.db, self.bot.cache).configure_temp_voice(
            interaction.guild.id,
            hub.id,
            category.id if category else None,
            name_format[:100],
            user_limit,
        )
        await interaction.response.send_message(
            f"Temporary voice hub configured at {hub.mention}.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is None or before.channel == after.channel:
            return
        channel = await CommunityService(self.bot.db, self.bot.cache).create_temp_voice(
            member.guild,
            member,
            after.channel.id,
        )
        if channel is not None:
            return


async def setup(bot):
    await bot.add_cog(Engagement(bot))

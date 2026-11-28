"""Minecraft economy commands.

The economy is server-scoped and deliberately simple: emeralds live in the
existing ledger-backed wallet, the bank is a second pocket, and every wager or
transfer is validated by :class:`bot.services.economy.EconomyService` before it
touches the database.

Commands that already exist as root commands (``/balance``, ``/daily`` and
``/coinflip``) are kept there for backwards compatibility.  This cog exposes the
full economy surface under ``/economy`` without re-registering those names.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.interactions import safe_defer, safe_send
from bot.ui import error_embed, info_embed, success_embed, warning_embed

DAILY_SECONDS = 86_400
WEEKLY_SECONDS = 604_800
WORK_SECONDS = 3_600


def _coins(amount: int) -> str:
    return f"🟢 **{amount:,}** emeralds"


def _net_line(net: int) -> str:
    if net > 0:
        return f"Profit: {_coins(net)}"
    if net < 0:
        return f"Loss: 🔴 **{abs(net):,}** emeralds"
    return "You broke even."


class Economy(commands.GroupCog, name="economy"):
    """Earn, bank, transfer and gamble emeralds."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def economy(self):
        return self.bot.economy

    async def _cooldown(self, interaction, key: str, seconds: int) -> bool:
        limiter = getattr(self.bot, "limiter", None)
        if limiter is None:
            return True
        return await limiter.allow(key, 1, seconds)

    @staticmethod
    async def _error(interaction, title: str, error: Exception) -> None:
        await safe_send(interaction, embed=error_embed(title, str(error)), ephemeral=True)

    # ------------------------------------------------------------------
    # Balances and rewards
    # ------------------------------------------------------------------
    @app_commands.command(name="balance", description="Show your wallet and bank balance")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to inspect")
    async def balance(self, interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        wallet, bank = await self.economy.balance(interaction.guild.id, member.id)
        embed = info_embed(
            f"🟢 {member.display_name}'s Emerald Pouch",
            f"{member.mention} keeps their emeralds close.",
        )
        embed.add_field(name="Wallet", value=f"**{wallet:,}**", inline=True)
        embed.add_field(name="Bank", value=f"**{bank:,}**", inline=True)
        embed.add_field(name="Total", value=f"**{wallet + bank:,}**", inline=True)
        await safe_send(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="Claim your daily emerald reward")
    @app_commands.guild_only()
    async def daily(self, interaction: discord.Interaction):
        key = f"economy:daily:{interaction.guild.id}:{interaction.user.id}"
        if not await self._cooldown(interaction, key, DAILY_SECONDS):
            return await safe_send(
                interaction,
                embed=warning_embed("Daily already claimed", "The daily chest refills once every 24 hours."),
                ephemeral=True,
            )
        await safe_defer(interaction)
        try:
            reward, wallet = await self.economy.daily(
                interaction.guild.id,
                interaction.user.id,
                f"{key}:{datetime.now(UTC):%Y-%m-%d}",
            )
        except ValueError as error:
            return await self._error(interaction, "Daily reward", error)
        embed = success_embed("Daily reward", f"You found {_coins(reward)} near the village chest.")
        embed.add_field(name="Wallet", value=f"**{wallet:,}**", inline=True)
        await safe_send(interaction, embed=embed)

    @app_commands.command(name="weekly", description="Claim your weekly emerald reward")
    @app_commands.guild_only()
    async def weekly(self, interaction: discord.Interaction):
        key = f"economy:weekly:{interaction.guild.id}:{interaction.user.id}"
        if not await self._cooldown(interaction, key, WEEKLY_SECONDS):
            return await safe_send(
                interaction,
                embed=warning_embed("Weekly already claimed", "The weekly vault refills once every seven days."),
                ephemeral=True,
            )
        await safe_defer(interaction)
        try:
            reward, wallet = await self.economy.weekly(
                interaction.guild.id,
                interaction.user.id,
                f"{key}:{datetime.now(UTC):%G-W%V}",
            )
        except ValueError as error:
            return await self._error(interaction, "Weekly reward", error)
        embed = success_embed("Weekly reward", f"The vault yielded {_coins(reward)}.")
        embed.add_field(name="Wallet", value=f"**{wallet:,}**", inline=True)
        await safe_send(interaction, embed=embed)

    @commands.hybrid_command(name="work", description="Work a job for emeralds")
    @commands.guild_only()
    async def work(self, ctx: commands.Context):
        key = f"economy:work:{ctx.guild.id}:{ctx.author.id}"
        if not await self._cooldown(ctx, key, WORK_SECONDS):
            return await ctx.send(
                embed=warning_embed("Still working", "You can take another job in about an hour."),
                ephemeral=True,
            )
        await ctx.defer(ephemeral=True)
        try:
            action, reward, wallet = await self.economy.work(
                ctx.guild.id,
                ctx.author.id,
                f"{key}:{uuid.uuid4().hex}",
            )
        except ValueError as error:
            return await ctx.send(embed=error_embed("Work", str(error)), ephemeral=True)
        embed = success_embed("Honest work", f"You {action} and earned {_coins(reward)}.")
        embed.add_field(name="Wallet", value=f"**{wallet:,}**", inline=True)
        await ctx.send(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # Banking and transfers
    # ------------------------------------------------------------------
    @commands.hybrid_command(name="deposit", description="Move emeralds from your wallet into the bank")
    @commands.guild_only()
    @app_commands.describe(amount="Amount of emeralds to deposit")
    async def deposit(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            return await ctx.send(embed=error_embed("Deposit", "Choose a positive amount."), ephemeral=True)
        try:
            wallet, bank = await self.economy.deposit(ctx.guild.id, ctx.author.id, amount)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Deposit", str(error)), ephemeral=True)
        embed = success_embed("Deposit complete", f"You stored {_coins(amount)} in the bank.")
        embed.add_field(name="Wallet", value=f"**{wallet:,}**", inline=True)
        embed.add_field(name="Bank", value=f"**{bank:,}**", inline=True)
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="withdraw", description="Move emeralds from the bank into your wallet")
    @commands.guild_only()
    @app_commands.describe(amount="Amount of emeralds to withdraw")
    async def withdraw(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            return await ctx.send(embed=error_embed("Withdraw", "Choose a positive amount."), ephemeral=True)
        try:
            wallet, bank = await self.economy.withdraw(ctx.guild.id, ctx.author.id, amount)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Withdraw", str(error)), ephemeral=True)
        embed = success_embed("Withdrawal complete", f"You took {_coins(amount)} out of the bank.")
        embed.add_field(name="Wallet", value=f"**{wallet:,}**", inline=True)
        embed.add_field(name="Bank", value=f"**{bank:,}**", inline=True)
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="pay", description="Send emeralds to another member")
    @commands.guild_only()
    @app_commands.describe(member="Member to pay", amount="Amount of emeralds to send")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        if member.bot:
            return await ctx.send(embed=error_embed("Payment", "Bots do not need emeralds."), ephemeral=True)
        if amount <= 0:
            return await ctx.send(embed=error_embed("Payment", "Choose a positive amount."), ephemeral=True)
        try:
            _, wallet = await self.economy.pay(
                ctx.guild.id,
                ctx.author.id,
                member.id,
                amount,
                f"pay:{ctx.guild.id}:{ctx.author.id}:{uuid.uuid4().hex}",
            )
        except ValueError as error:
            return await ctx.send(embed=error_embed("Payment", str(error)), ephemeral=True)
        embed = success_embed("Payment sent", f"{ctx.author.mention} sent {_coins(amount)} to {member.mention}.")
        embed.add_field(name="Your wallet", value=f"**{wallet:,}**", inline=True)
        await ctx.send(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the richest members on the server")
    @app_commands.guild_only()
    @app_commands.describe(limit="Number of members to show")
    async def leaderboard(self, interaction: discord.Interaction, limit: app_commands.Range[int, 1, 25] = 10):
        rows = await self.economy.leaderboard(interaction.guild.id, limit)
        if not rows:
            return await safe_send(
                interaction,
                embed=info_embed("Emerald Leaderboard", "Nobody has earned emeralds yet."),
                ephemeral=True,
            )
        lines = []
        for position, row in enumerate(rows, 1):
            member = interaction.guild.get_member(row.user_id)
            name = member.display_name if member else f"User {row.user_id}"
            lines.append(f"**#{position}** {name} — **{row.wallet + row.bank:,}** emeralds")
        await safe_send(
            interaction,
            embed=info_embed(f"{interaction.guild.name} • Emerald Leaderboard", "\n".join(lines)),
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # Gambling
    # ------------------------------------------------------------------
    @commands.hybrid_command(name="slots", description="Spin the emerald slots")
    @commands.guild_only()
    @app_commands.describe(bet="Emeralds to wager")
    async def slots(self, ctx: commands.Context, bet: int):
        await ctx.defer(ephemeral=True)
        try:
            result = await self.economy.slots(ctx.guild.id, ctx.author.id, bet)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Slots", str(error)), ephemeral=True)
        reels = " | ".join(result["reels"])
        if result["multiplier"] == 0:
            description = f"{reels}\n\nNo line this time. {_net_line(result['net'])}"
        else:
            description = f"{reels}\n\n**x{result['multiplier']}** — {_coins(result['payout'])}\n{_net_line(result['net'])}"
        await ctx.send(embed=info_embed("🎰 Emerald Slots", description), ephemeral=True)

    @commands.hybrid_command(name="roulette", description="Bet on a roulette colour, parity or number")
    @commands.guild_only()
    @app_commands.describe(bet="Emeralds to wager", choice="red, black, green, even, odd, or 0-36")
    async def roulette(self, ctx: commands.Context, bet: int, choice: str):
        await ctx.defer(ephemeral=True)
        try:
            result = await self.economy.roulette(ctx.guild.id, ctx.author.id, bet, choice)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Roulette", str(error)), ephemeral=True)
        colour = result["colour"].title()
        description = (
            f"The wheel lands on **{result['number']} {colour}**.\n"
            f"{_coins(result['payout']) if result['payout'] else 'No payout.'}\n"
            f"{_net_line(result['net'])}"
        )
        await ctx.send(embed=info_embed("🎡 Roulette", description), ephemeral=True)

    @commands.hybrid_command(name="guess", description="Guess a number between 1 and 10")
    @commands.guild_only()
    @app_commands.describe(bet="Emeralds to wager", number="Your guess from 1 to 10")
    async def guess(self, ctx: commands.Context, bet: int, number: int):
        await ctx.defer(ephemeral=True)
        try:
            result = await self.economy.guess(ctx.guild.id, ctx.author.id, bet, number)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Guess", str(error)), ephemeral=True)
        if result["won"]:
            description = f"The number was **{result['rolled']}**. You called it.\n{_coins(result['payout'])}"
        else:
            description = f"The number was **{result['rolled']}**. Better luck next time.\n{_net_line(result['net'])}"
        await ctx.send(embed=info_embed("🔢 Number Guess", description), ephemeral=True)

    @commands.hybrid_command(name="blackjack", description="Play a quick hand of blackjack")
    @commands.guild_only()
    @app_commands.describe(bet="Emeralds to wager")
    async def blackjack(self, ctx: commands.Context, bet: int):
        await ctx.defer(ephemeral=True)
        try:
            result = await self.economy.blackjack(ctx.guild.id, ctx.author.id, bet)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Blackjack", str(error)), ephemeral=True)
        labels = {
            "win": "You win.",
            "lose": "The dealer wins.",
            "push": "A push — your wager is returned.",
            "bust": "You bust.",
        }
        description = (
            f"**You:** {' '.join(map(str, result['player']))} = **{result['player_value']}**\n"
            f"**Dealer:** {' '.join(map(str, result['dealer']))} = **{result['dealer_value']}**\n\n"
            f"{labels.get(result['result'], result['result'])}\n"
            f"{_coins(result['payout']) if result['payout'] else 'No payout.'}"
        )
        await ctx.send(embed=info_embed("🃏 Blackjack", description), ephemeral=True)

    @commands.hybrid_command(name="lottery", description="Buy a lottery ticket for a shot at the jackpot")
    @commands.guild_only()
    async def lottery(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        try:
            result = await self.economy.lottery(ctx.guild.id, ctx.author.id)
        except ValueError as error:
            return await ctx.send(embed=error_embed("Lottery", str(error)), ephemeral=True)
        if result["won"]:
            description = f"The ticket matches. {_coins(result['payout'])}"
        else:
            description = "The ticket does not match. The jackpot rolls on."
        await ctx.send(embed=info_embed("🎟️ Lottery", description), ephemeral=True)

    @commands.hybrid_command(name="rob", description="Try to take emeralds from another member")
    @commands.guild_only()
    @app_commands.describe(member="Member to rob")
    async def rob(self, ctx: commands.Context, member: discord.Member):
        if member.bot:
            return await ctx.send(embed=error_embed("Robbery", "Bots keep their emeralds in a vault."), ephemeral=True)
        await ctx.defer(ephemeral=True)
        try:
            result = await self.economy.rob(
                ctx.guild.id,
                ctx.author.id,
                member.id,
                f"rob:{ctx.guild.id}:{ctx.author.id}:{uuid.uuid4().hex}",
            )
        except ValueError as error:
            return await ctx.send(embed=error_embed("Robbery", str(error)), ephemeral=True)
        if result["success"]:
            description = f"You slipped away with {_coins(result['amount'])} from {member.mention}."
        elif result["penalty"]:
            description = f"You were caught and paid {_coins(result['penalty'])} to {member.mention}."
        else:
            description = f"You were caught, but {member.mention} found nothing worth fining."
        await ctx.send(embed=info_embed("🥷 Robbery", description), ephemeral=True)

    @commands.hybrid_command(name="cookie", description="Give a cookie to another member")
    @commands.guild_only()
    @app_commands.describe(member="Member to gift")
    async def cookie(self, ctx: commands.Context, member: discord.Member):
        if member.bot:
            return await ctx.send(embed=error_embed("Cookie", "Bots cannot eat cookies."), ephemeral=True)
        try:
            await self.economy.cookie(
                ctx.guild.id,
                ctx.author.id,
                member.id,
                f"cookie:{ctx.guild.id}:{ctx.author.id}:{uuid.uuid4().hex}",
            )
        except ValueError as error:
            return await ctx.send(embed=error_embed("Cookie", str(error)), ephemeral=True)
        await ctx.send(embed=success_embed("Cookie gifted", f"{member.mention} received a cookie from {ctx.author.mention}."))

    @commands.hybrid_command(name="curse", description="Spend emeralds to curse another member's luck")
    @commands.guild_only()
    @app_commands.describe(member="Member to curse")
    async def curse(self, ctx: commands.Context, member: discord.Member):
        if member.bot:
            return await ctx.send(embed=error_embed("Curse", "Bots are already cursed."), ephemeral=True)
        try:
            await self.economy.curse(
                ctx.guild.id,
                ctx.author.id,
                member.id,
                f"curse:{ctx.guild.id}:{ctx.author.id}:{uuid.uuid4().hex}",
            )
        except ValueError as error:
            return await ctx.send(embed=error_embed("Curse", str(error)), ephemeral=True)
        await ctx.send(
            embed=warning_embed(
                "Curse cast",
                f"{member.mention} has been cursed with bad luck for an hour.",
            )
        )


async def setup(bot):
    bot.economy_cog = Economy(bot)
    await bot.add_cog(bot.economy_cog)

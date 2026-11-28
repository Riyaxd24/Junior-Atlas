from __future__ import annotations

import random

from bot.repositories.economy import EconomyRepository

SLOT_SYMBOLS = ("🍒", "🍋", "🔔", "💎", "⭐", "🍀")
ROULETTE_COLOURS = ("red", "black", "green")


class EconomyService:
    def __init__(self, db, cache=None, rng=None):
        self.repository = EconomyRepository(db)
        self.cache = cache
        self.rng = rng or random.Random()

    # ------------------------------------------------------------------
    # Balance primitives
    # ------------------------------------------------------------------
    async def balance(self, guild_id, user_id):
        account = await self.repository.get_or_create(guild_id, user_id)
        return account.wallet, account.bank

    async def wallet(self, guild_id, user_id):
        account = await self.repository.get_or_create(guild_id, user_id)
        return account.wallet

    async def credit(
        self,
        guild_id,
        user_id,
        amount,
        *,
        source,
        description,
        idempotency_key=None,
    ):
        if amount <= 0:
            raise ValueError("Credit amount must be positive.")
        return await self.repository.modify_wallet(
            guild_id,
            user_id,
            amount=amount,
            source=source,
            description=description,
            idempotency_key=idempotency_key,
        )

    async def debit(
        self,
        guild_id,
        user_id,
        amount,
        *,
        source,
        description,
        idempotency_key=None,
    ):
        if amount <= 0:
            raise ValueError("Debit amount must be positive.")
        return await self.repository.modify_wallet(
            guild_id,
            user_id,
            amount=-amount,
            source=source,
            description=description,
            idempotency_key=idempotency_key,
        )

    async def daily(self, guild_id, user_id, idempotency_key):
        reward = self.rng.randint(200, 500)
        wallet = await self.credit(
            guild_id,
            user_id,
            reward,
            source="daily",
            description="Daily currency reward",
            idempotency_key=idempotency_key,
        )
        return reward, wallet

    async def weekly(self, guild_id, user_id, idempotency_key):
        reward = self.rng.randint(1500, 3000)
        wallet = await self.credit(
            guild_id,
            user_id,
            reward,
            source="weekly",
            description="Weekly currency reward",
            idempotency_key=idempotency_key,
        )
        return reward, wallet

    async def work(self, guild_id, user_id, idempotency_key):
        jobs = [
            ("delivered pizzas", 50, 150),
            ("wrote code", 80, 200),
            ("fixed a server outage", 100, 250),
        ]
        action, low, high = self.rng.choice(jobs)
        reward = self.rng.randint(low, high)
        wallet = await self.credit(
            guild_id,
            user_id,
            reward,
            source="work",
            description=f"Worked: {action}",
            idempotency_key=idempotency_key,
        )
        return action, reward, wallet

    async def deposit(self, guild_id, user_id, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        return await self.repository.deposit(guild_id, user_id, amount)

    async def withdraw(self, guild_id, user_id, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        return await self.repository.withdraw(guild_id, user_id, amount)

    async def pay(self, guild_id, sender_id, recipient_id, amount, idempotency_key):
        return await self.repository.transfer(
            guild_id,
            sender_id,
            recipient_id,
            amount,
            idempotency_key,
        )

    async def leaderboard(self, guild_id, limit=10):
        return await self.repository.leaderboard(guild_id, limit)

    # ------------------------------------------------------------------
    # Gambling
    # ------------------------------------------------------------------
    async def slots(self, guild_id, user_id, bet):
        if bet <= 0:
            raise ValueError("Bet must be positive.")
        await self.debit(
            guild_id,
            user_id,
            bet,
            source="slots",
            description="Slots wager",
        )
        reels = [self.rng.choice(SLOT_SYMBOLS) for _ in range(3)]
        if reels[0] == reels[1] == reels[2]:
            multiplier = 10 if reels[0] == "💎" else 5
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            multiplier = 2
        else:
            multiplier = 0
        payout = bet * multiplier
        if payout:
            await self.credit(
                guild_id,
                user_id,
                payout,
                source="slots",
                description="Slots payout",
            )
        return {
            "reels": reels,
            "payout": payout,
            "net": payout - bet,
            "multiplier": multiplier,
        }

    async def roulette(self, guild_id, user_id, bet, choice):
        if bet <= 0:
            raise ValueError("Bet must be positive.")
        choice = (choice or "").strip().lower()
        if choice not in (*ROULETTE_COLOURS, "even", "odd") and not choice.isdigit():
            raise ValueError("Choose red, black, green, even, odd, or a number from 0 to 36.")
        if choice.isdigit() and not 0 <= int(choice) <= 36:
            raise ValueError("Roulette numbers run from 0 to 36.")
        await self.debit(
            guild_id,
            user_id,
            bet,
            source="roulette",
            description="Roulette wager",
        )
        number = self.rng.randint(0, 36)
        if number == 0:
            colour = "green"
        elif number % 2 == 0:
            colour = "black"
        else:
            colour = "red"
        if choice == colour:
            multiplier = 14 if colour == "green" else 2
        elif choice == "even" and number != 0 and number % 2 == 0:
            multiplier = 2
        elif choice == "odd" and number % 2 == 1:
            multiplier = 2
        elif choice.isdigit() and int(choice) == number:
            multiplier = 36
        else:
            multiplier = 0
        payout = bet * multiplier
        if payout:
            await self.credit(
                guild_id,
                user_id,
                payout,
                source="roulette",
                description="Roulette payout",
            )
        return {
            "number": number,
            "colour": colour,
            "payout": payout,
            "net": payout - bet,
            "multiplier": multiplier,
        }

    async def guess(self, guild_id, user_id, bet, number):
        if bet <= 0:
            raise ValueError("Bet must be positive.")
        if not 1 <= number <= 10:
            raise ValueError("Guess a number from 1 to 10.")
        await self.debit(
            guild_id,
            user_id,
            bet,
            source="guess",
            description="Number guess wager",
        )
        rolled = self.rng.randint(1, 10)
        won = rolled == number
        payout = bet * 8 if won else 0
        if payout:
            await self.credit(
                guild_id,
                user_id,
                payout,
                source="guess",
                description="Number guess payout",
            )
        return {"rolled": rolled, "won": won, "payout": payout, "net": payout - bet}

    async def blackjack(self, guild_id, user_id, bet):
        if bet <= 0:
            raise ValueError("Bet must be positive.")
        await self.debit(
            guild_id,
            user_id,
            bet,
            source="blackjack",
            description="Blackjack wager",
        )
        player = [self._card(), self._card()]
        dealer = [self._card(), self._card()]
        while self._hand_value(player) < 17:
            player.append(self._card())
        while self._hand_value(dealer) < 17:
            dealer.append(self._card())
        player_value = self._hand_value(player)
        dealer_value = self._hand_value(dealer)
        if player_value > 21:
            result = "bust"
            payout = 0
        elif dealer_value > 21 or player_value > dealer_value:
            result = "win"
            payout = bet * 2
        elif player_value == dealer_value:
            result = "push"
            payout = bet
        else:
            result = "lose"
            payout = 0
        if payout:
            await self.credit(
                guild_id,
                user_id,
                payout,
                source="blackjack",
                description="Blackjack payout",
            )
        return {
            "player": player,
            "dealer": dealer,
            "player_value": player_value,
            "dealer_value": dealer_value,
            "result": result,
            "payout": payout,
            "net": payout - bet,
        }

    def _card(self):
        return self.rng.randint(1, 11)

    @staticmethod
    def _hand_value(hand):
        value = sum(hand)
        aces = hand.count(11)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    async def lottery(self, guild_id, user_id, ticket_price=500, jackpot=10000):
        if ticket_price <= 0:
            raise ValueError("Ticket price must be positive.")
        await self.debit(
            guild_id,
            user_id,
            ticket_price,
            source="lottery",
            description="Lottery ticket",
        )
        won = self.rng.random() < 0.02
        payout = jackpot if won else 0
        if payout:
            await self.credit(
                guild_id,
                user_id,
                payout,
                source="lottery",
                description="Lottery jackpot",
            )
        return {"won": won, "payout": payout, "net": payout - ticket_price}

    async def rob(self, guild_id, robber_id, target_id, idempotency_key):
        if robber_id == target_id:
            raise ValueError("You cannot rob yourself.")
        target = await self.repository.get_or_create(guild_id, target_id)
        if target.wallet <= 0:
            raise ValueError("That player has nothing worth taking.")
        success = self.rng.random() < 0.45
        if success:
            amount = max(1, int(target.wallet * self.rng.uniform(0.1, 0.25)))
            amount = min(amount, target.wallet)
            await self.repository.transfer(
                guild_id,
                target_id,
                robber_id,
                amount,
                f"{idempotency_key}:rob",
            )
            return {"success": True, "amount": amount, "penalty": 0}
        penalty = max(1, int(target.wallet * 0.05))
        robber = await self.repository.get_or_create(guild_id, robber_id)
        penalty = min(penalty, robber.wallet)
        if penalty:
            await self.repository.transfer(
                guild_id,
                robber_id,
                target_id,
                penalty,
                f"{idempotency_key}:fine",
            )
        return {"success": False, "amount": 0, "penalty": penalty}

    async def cookie(self, guild_id, sender_id, recipient_id, idempotency_key):
        if sender_id == recipient_id:
            raise ValueError("You cannot gift a cookie to yourself.")
        return await self.repository.transfer(
            guild_id,
            sender_id,
            recipient_id,
            50,
            idempotency_key,
        )

    async def curse(self, guild_id, sender_id, target_id, idempotency_key):
        if sender_id == target_id:
            raise ValueError("You cannot curse yourself.")
        await self.debit(
            guild_id,
            sender_id,
            100,
            source="curse",
            description="Curse ritual",
            idempotency_key=idempotency_key,
        )
        if self.cache is not None:
            try:
                await self.cache.set_json(
                    f"rpg:curse:{guild_id}:{target_id}",
                    {"by": sender_id},
                    ttl=3600,
                )
            except Exception:
                pass
        return True

from __future__ import annotations

import random

from bot.repositories.economy import EconomyRepository


class EconomyService:
    def __init__(self, db, cache=None):
        self.repository = EconomyRepository(db)
        self.cache = cache

    async def balance(self, guild_id, user_id):
        account = await self.repository.get_or_create(guild_id, user_id)
        return account.wallet, account.bank

    async def daily(self, guild_id, user_id, idempotency_key):
        reward = random.randint(200, 500)
        wallet = await self.repository.modify_wallet(
            guild_id,
            user_id,
            amount=reward,
            source="daily",
            description="Daily currency reward",
            idempotency_key=idempotency_key,
        )
        return reward, wallet

    async def weekly(self, guild_id, user_id, idempotency_key):
        reward = random.randint(1500, 3000)
        wallet = await self.repository.modify_wallet(
            guild_id,
            user_id,
            amount=reward,
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
        action, low, high = random.choice(jobs)
        reward = random.randint(low, high)
        wallet = await self.repository.modify_wallet(
            guild_id,
            user_id,
            amount=reward,
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

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import Economy, EconomyTransaction


class EconomyRepository:
    def __init__(self, db):
        self.db = db

    async def get_or_create(self, guild_id, user_id):
        async with self.db.session() as session:
            await session.execute(
                pg_insert(Economy)
                .values(guild_id=guild_id, user_id=user_id, balance=0, wallet=0, bank=0)
                .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            )
            account = await session.scalar(
                select(Economy)
                .where(
                    Economy.guild_id == guild_id,
                    Economy.user_id == user_id,
                )
                .with_for_update()
            )
            return account

    async def modify_wallet(
        self,
        guild_id,
        user_id,
        *,
        amount,
        source,
        description,
        idempotency_key=None,
        destination_user_id=None,
    ):
        if idempotency_key:
            async with self.db.session() as check_session:
                existing = await check_session.scalar(
                    select(EconomyTransaction).where(
                        EconomyTransaction.idempotency_key == idempotency_key
                    )
                )
                if existing is not None:
                    account = await self.get_or_create(guild_id, user_id)
                    return account.wallet
        async with self.db.session() as session:
            await session.execute(
                pg_insert(Economy)
                .values(guild_id=guild_id, user_id=user_id, balance=0, wallet=0, bank=0)
                .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            )
            account = await session.scalar(
                select(Economy)
                .where(
                    Economy.guild_id == guild_id,
                    Economy.user_id == user_id,
                )
                .with_for_update()
            )
            next_wallet = account.wallet + amount
            if next_wallet < 0:
                raise ValueError("Insufficient balance.")
            account.wallet = next_wallet
            account.balance = next_wallet
            session.add(
                EconomyTransaction(
                    guild_id=guild_id,
                    user_id=user_id,
                    amount=amount,
                    source=source,
                    destination_user_id=destination_user_id,
                    balance_after=next_wallet,
                    idempotency_key=idempotency_key,
                    description=description,
                )
            )
            await session.commit()
            await session.refresh(account)
            return account.wallet

    async def transfer(self, guild_id, sender_id, recipient_id, amount, idempotency_key):
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        if sender_id == recipient_id:
            raise ValueError("You cannot pay yourself.")
        async with self.db.session() as check_session:
            existing = await check_session.scalar(
                select(EconomyTransaction).where(
                    EconomyTransaction.idempotency_key == idempotency_key
                )
            )
            if existing is not None:
                return True, existing.balance_after
        async with self.db.session() as session:
            for user_id in (sender_id, recipient_id):
                await session.execute(
                    pg_insert(Economy)
                    .values(guild_id=guild_id, user_id=user_id, balance=0, wallet=0, bank=0)
                    .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
                )
            result = await session.execute(
                select(Economy)
                .where(
                    Economy.guild_id == guild_id,
                    Economy.user_id.in_((sender_id, recipient_id)),
                )
                .order_by(Economy.user_id)
                .with_for_update()
            )
            accounts = {row.user_id: row for row in result.scalars()}
            sender_account = accounts[sender_id]
            recipient_account = accounts[recipient_id]
            if sender_account.wallet < amount:
                raise ValueError("Insufficient balance.")
            sender_account.wallet -= amount
            sender_account.balance = sender_account.wallet
            recipient_account.wallet += amount
            recipient_account.balance = recipient_account.wallet
            session.add_all([
                EconomyTransaction(
                    guild_id=guild_id,
                    user_id=sender_id,
                    amount=-amount,
                    source="pay",
                    destination_user_id=recipient_id,
                    balance_after=sender_account.wallet,
                    idempotency_key=idempotency_key,
                    description="Outgoing payment",
                ),
                EconomyTransaction(
                    guild_id=guild_id,
                    user_id=recipient_id,
                    amount=amount,
                    source="pay",
                    destination_user_id=sender_id,
                    balance_after=recipient_account.wallet,
                    idempotency_key=f"{idempotency_key}:recipient",
                    description="Incoming payment",
                ),
            ])
            await session.commit()
            return False, sender_account.wallet

    async def leaderboard(self, guild_id, limit=10):
        async with self.db.session() as session:
            rows = (
                await session.execute(
                    select(Economy)
                    .where(Economy.guild_id == guild_id)
                    .order_by((Economy.wallet + Economy.bank).desc())
                    .limit(limit)
                )
            ).scalars().all()
            return list(rows)

    async def deposit(self, guild_id, user_id, amount):
        async with self.db.session() as session:
            await session.execute(
                pg_insert(Economy)
                .values(guild_id=guild_id, user_id=user_id, balance=0, wallet=0, bank=0)
                .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            )
            account = await session.scalar(
                select(Economy)
                .where(Economy.guild_id == guild_id, Economy.user_id == user_id)
                .with_for_update()
            )
            if account.wallet < amount:
                raise ValueError("Insufficient wallet balance.")
            account.wallet -= amount
            account.bank += amount
            account.balance = account.wallet
            await session.commit()
            return account.wallet, account.bank

    async def withdraw(self, guild_id, user_id, amount):
        async with self.db.session() as session:
            await session.execute(
                pg_insert(Economy)
                .values(guild_id=guild_id, user_id=user_id, balance=0, wallet=0, bank=0)
                .on_conflict_do_nothing(index_elements=["guild_id", "user_id"])
            )
            account = await session.scalar(
                select(Economy)
                .where(Economy.guild_id == guild_id, Economy.user_id == user_id)
                .with_for_update()
            )
            if account.bank < amount:
                raise ValueError("Insufficient bank balance.")
            account.bank -= amount
            account.wallet += amount
            account.balance = account.wallet
            await session.commit()
            return account.wallet, account.bank

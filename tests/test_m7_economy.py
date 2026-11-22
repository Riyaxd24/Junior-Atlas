from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.services.economy import EconomyService


@pytest.mark.asyncio
async def test_economy_rejects_self_payment_and_non_positive_amount():
    service = EconomyService(SimpleNamespace(), cache=None)
    service.repository.transfer = AsyncMock(
        side_effect=[ValueError("You cannot pay yourself."), ValueError("Payment amount must be positive.")]
    )

    with pytest.raises(ValueError, match="pay yourself"):
        await service.pay(1, 2, 2, 100, "key")
    with pytest.raises(ValueError, match="positive"):
        await service.pay(1, 2, 3, 0, "key")


@pytest.mark.asyncio
async def test_economy_work_and_rewards_are_positive():
    service = EconomyService(SimpleNamespace(), cache=None)
    service.repository.modify_wallet = AsyncMock(return_value=350)

    action, reward, wallet = await service.work(1, 2, "work-key")

    assert action
    assert reward > 0
    assert wallet == 350


@pytest.mark.asyncio
async def test_economy_deposit_and_withdraw_use_positive_amounts():
    service = EconomyService(SimpleNamespace(), cache=None)
    service.repository.deposit = AsyncMock(return_value=(50, 50))
    service.repository.withdraw = AsyncMock(return_value=(100, 0))

    assert await service.deposit(1, 2, 50) == (50, 50)
    assert await service.withdraw(1, 2, 50) == (100, 0)
    with pytest.raises(ValueError, match="positive"):
        await service.deposit(1, 2, 0)

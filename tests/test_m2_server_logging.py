from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.services.server_logging import ServerLoggingService


@pytest.mark.asyncio
async def test_disabled_event_is_not_persisted():
    service = ServerLoggingService(SimpleNamespace(), cache=None)
    service.repository.get_configuration = AsyncMock(
        return_value=(
            [SimpleNamespace(event_type="message_delete", channel_id=5, enabled=False)],
            None,
        )
    )
    service.repository.add_record = AsyncMock()

    delivery = await service.prepare_event(
        1,
        "message_delete",
        "Deleted",
        "A message was deleted.",
    )

    assert delivery is None
    service.repository.add_record.assert_not_awaited()


@pytest.mark.asyncio
async def test_message_content_is_opt_in():
    service = ServerLoggingService(SimpleNamespace(), cache=None)
    service.repository.get_configuration = AsyncMock(
        return_value=(
            [SimpleNamespace(event_type="message_delete", channel_id=5, enabled=True)],
            SimpleNamespace(
                include_message_content=True,
                retention_days=14,
                exempt_channel_ids=[],
            ),
        )
    )
    service.repository.add_record = AsyncMock()
    service.repository.delete_expired_records = AsyncMock(return_value=0)

    delivery = await service.prepare_event(
        1,
        "message_delete",
        "Deleted",
        "A message was deleted.",
        message_content="x" * 1500,
        bot_authored=False,
    )

    record = service.repository.add_record.await_args.args[0]
    assert delivery is not None
    assert record.content == "x" * 1000


@pytest.mark.asyncio
async def test_bot_message_content_is_never_retained():
    service = ServerLoggingService(SimpleNamespace(), cache=None)
    service.repository.get_configuration = AsyncMock(
        return_value=(
            [SimpleNamespace(event_type="message_delete", channel_id=5, enabled=True)],
            SimpleNamespace(
                include_message_content=True,
                retention_days=14,
                exempt_channel_ids=[],
            ),
        )
    )
    service.repository.add_record = AsyncMock()
    service.repository.delete_expired_records = AsyncMock(return_value=0)

    delivery = await service.prepare_event(
        1,
        "message_delete",
        "Deleted",
        "A message was deleted.",
        message_content="bot text",
        bot_authored=True,
    )

    record = service.repository.add_record.await_args.args[0]
    assert delivery is not None
    assert record.content is None


@pytest.mark.asyncio
async def test_exempt_channel_is_not_logged():
    service = ServerLoggingService(SimpleNamespace(), cache=None)
    service.repository.get_configuration = AsyncMock(
        return_value=(
            [SimpleNamespace(event_type="message_delete", channel_id=5, enabled=True)],
            SimpleNamespace(
                include_message_content=True,
                retention_days=14,
                exempt_channel_ids=[22],
            ),
        )
    )
    service.repository.add_record = AsyncMock()

    delivery = await service.prepare_event(
        1,
        "message_delete",
        "Deleted",
        "A message was deleted.",
        channel_id=22,
        message_content="private",
    )

    assert delivery is None
    service.repository.add_record.assert_not_awaited()

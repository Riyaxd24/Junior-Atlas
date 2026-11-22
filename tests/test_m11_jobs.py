import pytest

from bot.workers.arq import WorkerSettings, ping


@pytest.mark.asyncio
async def test_arq_ping_is_stable():
    assert await ping({}) == "pong"


def test_arq_worker_registers_cleanup_jobs():
    names = {function.__name__ for function in WorkerSettings.functions}
    assert {"ping", "cleanup_server_logs", "cleanup_automod_message_events", "cleanup_temp_roles"} <= names
    assert len(WorkerSettings.cron_jobs) == 3

from pathlib import Path

import aiohttp
import pytest

from bot.core.bot import Bot
from bot.core.config import Settings
from bot.core.health import start_health_server


def test_dashboard_is_disabled_by_default():
    assert Settings().dashboard_enabled is False


@pytest.mark.asyncio
async def test_bot_does_not_construct_dashboard_by_default():
    bot = Bot(Settings(token='test-token'))
    try:
        assert bot.dashboard is None
    finally:
        await bot.cache.close()
        await bot.db.close()


def test_dashboard_import_and_start_are_explicitly_gated():
    source = Path('bot/core/bot.py').read_text()
    assert 'self.dashboard = None' in source
    assert 'if settings.dashboard_enabled:' in source
    assert 'if self.dashboard is not None:' in source
    assert '\nfrom bot.web.api import DashboardAPI' not in source
    assert 'from bot.web.api import DashboardAPI' in source


def test_health_and_readiness_endpoints_remain_available():
    source = Path('bot/core/health.py').read_text()
    assert '/healthz' in source
    assert '/readyz' in source
    assert 'start_health_server' in source


def test_dashboard_source_remains_importable_for_future_work():
    from bot.web.api import DashboardAPI

    assert DashboardAPI is not None


class _Dependency:
    def __init__(self, healthy=True):
        self.healthy = healthy

    async def health(self):
        if not self.healthy:
            raise RuntimeError('dependency unavailable')
        return True


class _HealthBot:
    def __init__(self, *, db_healthy=True, redis_healthy=True):
        self.db = _Dependency(db_healthy)
        self.cache = _Dependency(redis_healthy)
        self.shard_leases = type('Lease', (), {'healthy': True})()

    def is_ready(self):
        return True


async def _start_and_get(bot, path):
    runner = await start_health_server(bot, '127.0.0.1', 0)
    try:
        port = runner.addresses[0][1]
        async with (
            aiohttp.ClientSession() as session,
            session.get(f'http://127.0.0.1:{port}{path}') as response,
        ):
            return response.status, await response.json()
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_health_endpoint_reports_liveness():
    status, body = await _start_and_get(_HealthBot(), '/healthz')
    assert status == 200
    assert body == {'status': 'ok'}


@pytest.mark.asyncio
async def test_readiness_endpoint_reports_healthy_dependencies():
    status, body = await _start_and_get(_HealthBot(), '/readyz')
    assert status == 200
    assert body['status'] == 'ok'
    assert body['db'] is True
    assert body['redis'] is True


@pytest.mark.asyncio
async def test_readiness_endpoint_degrades_without_crashing():
    status, body = await _start_and_get(_HealthBot(db_healthy=False), '/readyz')
    assert status == 503
    assert body['status'] == 'degraded'
    assert body['db'] is False

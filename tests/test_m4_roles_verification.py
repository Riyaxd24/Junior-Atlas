from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.services.roles import RolesService


@pytest.mark.asyncio
async def test_temp_role_rejects_unassignable_role():
    service = RolesService(AsyncNamespaceDB())

    guild = SimpleNamespace(
        id=1,
        me=SimpleNamespace(top_role=SimpleNamespace(position=10)),
    )
    class FakeRole:
        managed = False

        def is_default(self):
            return False

        def __ge__(self, other):
            return True

    role = FakeRole()
    member = SimpleNamespace(add_roles=AsyncMock())

    with pytest.raises(ValueError):
        await service.assign_temp_role(
            guild,
            member,
            role,
            60,
            reason="test",
        )
    member.add_roles.assert_not_awaited()


@pytest.mark.asyncio
async def test_temp_role_persists_expiration():
    service = RolesService(AsyncNamespaceDB())
    service.repository.assign_temp_role = AsyncMock()
    guild = SimpleNamespace(
        id=1,
        me=SimpleNamespace(top_role=SimpleNamespace()),
    )
    class FakeRole:
        managed = False
        id = 9

        def is_default(self):
            return False

        def __ge__(self, other):
            return False

    role = FakeRole()
    member = SimpleNamespace(id=8, add_roles=AsyncMock())

    expires_at = await service.assign_temp_role(
        guild,
        member,
        role,
        60,
        reason="test",
    )

    member.add_roles.assert_awaited_once()
    service.repository.assign_temp_role.assert_awaited_once()
    assert expires_at is not None


class AsyncNamespaceDB:
    pass

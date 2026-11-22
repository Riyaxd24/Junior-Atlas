from types import SimpleNamespace

import pytest

from bot.core.app_errors import PermissionDenied
from bot.core.permissions import check_hierarchy, check_user_permissions
from bot.ui.views import ConfirmationView, EmbedPaginator


def test_hierarchy_rejects_owner_and_self():
    guild = SimpleNamespace(owner_id=10)
    owner = SimpleNamespace(id=10, guild=guild)
    target = SimpleNamespace(id=10, guild=guild)
    moderator = SimpleNamespace(id=20, guild=guild)

    with pytest.raises(PermissionDenied):
        check_hierarchy(owner, target)
    with pytest.raises(PermissionDenied):
        check_hierarchy(moderator, target)


def test_user_permissions_allow_owner_and_administrator():
    guild = SimpleNamespace(owner_id=10)
    owner = SimpleNamespace(
        id=10,
        guild=guild,
        guild_permissions=SimpleNamespace(administrator=False),
    )
    check_user_permissions(SimpleNamespace(), owner, ban_members=True)


def test_confirmation_and_paginator_have_safe_defaults():
    confirmation = ConfirmationView(author_id=10)
    assert confirmation.confirmed is None

    with pytest.raises(ValueError):
        EmbedPaginator([], author_id=10)

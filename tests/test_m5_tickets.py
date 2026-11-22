from types import SimpleNamespace

import pytest

from bot.repositories.tickets import TicketRepository


class FakeSessionContext:
    def __init__(self, ticket):
        self.ticket = ticket
        self.committed = False

    async def __aenter__(self):
        return SimpleNamespace(
            scalar=AsyncScalar(self.ticket),
            execute=None,
            commit=self.commit,
            refresh=self.refresh,
            add=lambda row: None,
        )

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self):
        self.committed = True

    async def refresh(self, row):
        return None


class AsyncScalar:
    def __init__(self, value):
        self.value = value

    async def __call__(self, statement):
        return self.value


@pytest.mark.asyncio
async def test_closed_ticket_rejects_invalid_claim_transition():
    ticket = SimpleNamespace(status="closed", claimed_by_id=None)
    db = SimpleNamespace(
        session=lambda: FakeSessionContext(ticket),
    )
    repo = TicketRepository(db)
    result = await repo.transition(1, status="claimed", user_id=2)
    assert result is None


@pytest.mark.asyncio
async def test_claim_then_close_then_reopen_is_stateful():
    ticket = SimpleNamespace(
        status="open",
        claimed_by_id=None,
        closed_by_id=None,
        closed_at=None,
        close_reason=None,
    )
    db = SimpleNamespace(session=lambda: FakeSessionContext(ticket))
    repo = TicketRepository(db)

    claimed = await repo.transition(1, status="claimed", user_id=2)
    assert claimed.status == "claimed"
    assert claimed.claimed_by_id == 2

    closed = await repo.transition(1, status="closed", user_id=2, reason="done")
    assert closed.status == "closed"

    reopened = await repo.transition(1, status="open")
    assert reopened.status == "open"

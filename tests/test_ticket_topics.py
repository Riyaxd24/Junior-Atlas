
from bot.services.tickets import TICKET_TOPIC_PREFIX, ticket_owner_id


def test_new_ticket_topic_prefix_is_used():
    assert TICKET_TOPIC_PREFIX == 'junior-atlas-ticket-owner:'
    assert ticket_owner_id('junior-atlas-ticket-owner:123') == 123


def test_legacy_ticket_topics_still_resolve_for_existing_channels():
    assert ticket_owner_id('fallen-ticket-owner:456') == 456
    assert ticket_owner_id('fallen-ticket-owner:456 extra metadata') == 456


def test_unknown_or_malformed_topics_are_rejected():
    assert ticket_owner_id(None) is None
    assert ticket_owner_id('') is None
    assert ticket_owner_id('unrelated') is None
    assert ticket_owner_id('junior-atlas-ticket-owner:not-an-id') is None

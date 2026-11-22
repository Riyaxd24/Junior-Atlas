from types import SimpleNamespace

from bot.services.security import AntiNukeService


def test_single_suspicious_event_alert_only():
    detector = AntiNukeService()
    result = detector.assess("channel_delete", 1, confidence=0.99)
    assert result["alert"] is True
    assert result["automate"] is False


def test_threshold_without_confidence_does_not_automate():
    detector = AntiNukeService()
    result = detector.assess("channel_delete", 3, confidence=0.50)
    assert result["alert"] is True
    assert result["automate"] is False


def test_threshold_and_confidence_automates():
    detector = AntiNukeService()
    result = detector.assess("channel_delete", 3, confidence=0.99)
    assert result["alert"] is True
    assert result["automate"] is True


def test_owner_and_administrator_are_trusted():
    detector = AntiNukeService()
    owner = SimpleNamespace(
        id=10,
        guild=SimpleNamespace(owner_id=10),
        guild_permissions=SimpleNamespace(administrator=False),
    )
    admin = SimpleNamespace(
        id=11,
        guild=SimpleNamespace(owner_id=10),
        guild_permissions=SimpleNamespace(administrator=True),
    )
    assert detector.trusted(owner) is True
    assert detector.trusted(admin) is True

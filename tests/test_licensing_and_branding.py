from pathlib import Path

from bot.core.bot import find_quarantine_role

ROOT = Path('.')


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_license_and_notice_exist_and_document_upstream():
    license_text = _read('LICENSE')
    notice_text = _read('NOTICE.md')
    assert 'All rights reserved' in license_text
    assert 'does not grant any rights' in license_text
    assert 'https://github.com/NOAH-NULL/FALLEN' in notice_text
    assert 'no LICENSE, COPYING, or NOTICE file' in notice_text
    assert 'Fallen-v1.2-uwuify.zip' in notice_text


def test_no_inherited_branding_in_active_runtime_files():
    # These two files intentionally retain pre-rebrand identifiers so existing
    # quarantined members and ticket channels keep working after the rename.
    compatibility_files = {
        Path('bot/core/bot.py'),
        Path('bot/services/tickets.py'),
    }
    offenders = []
    for path in Path('bot').rglob('*.py'):
        if path in compatibility_files:
            continue
        text = path.read_text(encoding='utf-8')
        for token in ('FALLEN', 'Fallen', 'discord-bot-v3', 'titan-discord-bot'):
            if token in text:
                offenders.append(f'{path}: {token}')
    assert offenders == []


def test_compatibility_identifiers_are_limited_to_documented_constants():
    bot_source = _read('bot/core/bot.py')
    ticket_source = _read('bot/services/tickets.py')
    assert bot_source.count('Fallen') == 1
    assert "LEGACY_QUARANTINE_ROLE_NAMES = ('Fallen Quarantine',)" in bot_source
    assert ticket_source.count('fallen-ticket-owner:') == 1
    assert 'LEGACY_TICKET_TOPIC_PREFIX = "fallen-ticket-owner:"' in ticket_source


def test_dashboard_session_storage_uses_new_brand_key():
    source = _read('bot/web/api.py')
    assert 'junior_atlas_key' in source
    assert 'fallen_key' not in source
    assert 'Junior Atlas • Command Center' in source


def test_quarantine_role_lookup_accepts_legacy_and_current_names():
    class Role:
        def __init__(self, name):
            self.name = name

    class Guild:
        def __init__(self, roles):
            self.roles = roles

    legacy = Role('Fallen Quarantine')
    current = Role('Junior Atlas Quarantine')
    assert find_quarantine_role(Guild([legacy])) is legacy
    assert find_quarantine_role(Guild([current])) is current
    assert find_quarantine_role(Guild([])) is None

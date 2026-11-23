from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.core.config import ConfigurationError, Settings, validate_startup


def _example_values():
    values = {}
    path = Path('.env.example')
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()
    return values


def test_env_example_has_no_duplicate_keys():
    keys = []
    for raw_line in Path('.env.example').read_text().splitlines():
        line = raw_line.strip()
        if line and not line.startswith('#') and '=' in line:
            keys.append(line.split('=', 1)[0].strip())
    duplicates = {key for key in keys if keys.count(key) > 1}
    assert duplicates == set()


def test_env_example_documents_every_settings_variable():
    documented = set(_example_values())
    required = set()
    for name, field in Settings.model_fields.items():
        alias = field.validation_alias
        if alias is not None and hasattr(alias, 'choices'):
            required.add(next(iter(alias.choices)))
        else:
            required.add(name.upper())
    assert required - documented == set()


def test_env_example_can_be_loaded_verbatim(monkeypatch):
    for key, value in _example_values().items():
        monkeypatch.setenv(key, value)
    settings = Settings()
    assert settings.dashboard_enabled is False
    assert settings.shard_count is None
    assert settings.instance_id
    assert settings.otel_service_name == 'junior-atlas'


def test_missing_discord_token_is_a_clear_configuration_error():
    for token in ('', '   '):
        with pytest.raises(ConfigurationError, match='DISCORD_TOKEN'):
            validate_startup(Settings(discord_token=token))


def test_valid_token_passes_startup_validation():
    validate_startup(Settings(discord_token='not-a-real-token'))


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'database_url': 'mysql://localhost/db'}, 'DATABASE_URL'),
        ({'redis_url': 'http://localhost:6379/0'}, 'REDIS_URL'),
        ({'log_level': 'verbose'}, 'LOG_LEVEL'),
        ({'metrics_port': 0}, 'greater than or equal to 1'),
        ({'gateway_queue_size': 10, 'gateway_critical_queue_size': 20}, 'GATEWAY_CRITICAL'),
    ],
)
def test_invalid_configuration_is_rejected(kwargs, message):
    with pytest.raises(ValidationError, match=message):
        Settings(**kwargs)


def test_empty_optional_values_are_normalized(monkeypatch):
    monkeypatch.setenv('SHARD_COUNT', '')
    monkeypatch.setenv('INSTANCE_ID', '')
    monkeypatch.setenv('GUILD_ID', '0')
    settings = Settings()
    assert settings.shard_count is None
    assert settings.guild_id is None
    assert settings.instance_id


def test_bot_owner_ids_must_be_positive():
    with pytest.raises(ValidationError, match='BOT_OWNER_IDS'):
        Settings(bot_owner_ids='-1')

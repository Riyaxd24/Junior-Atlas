from __future__ import annotations

import logging
import os
import uuid
from math import isfinite
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _i(k, d):
    try:
        return int(os.getenv(k, str(d)))
    except ValueError:
        return d

def _b(k, d=False):
    return os.getenv(k, str(d)).lower() in {'1', 'true', 'yes', 'on'}

def _f(k, d):
    try:
        value = float(os.getenv(k, str(d)))
        return value if isfinite(value) else d
    except (TypeError, ValueError):
        return d

def normalize_database_url(url: str) -> str:
    """Normalize Railway/standard PostgreSQL URLs for SQLAlchemy asyncio."""
    if url.startswith('postgres://'):
        return 'postgresql+asyncpg://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        return 'postgresql+asyncpg://' + url[len('postgresql://'):]
    return url


class ConfigurationError(RuntimeError):
    """Raised when runtime configuration cannot start a safe Discord session."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    discord_token: str = Field(
        default='',
        validation_alias=AliasChoices('DISCORD_TOKEN', 'discord_token', 'token'),
    )
    bot_owner_ids: Annotated[list[int], NoDecode] = Field(
        default_factory=list,
        validation_alias=AliasChoices('BOT_OWNER_IDS', 'bot_owner_ids'),
    )
    # Legacy-compatible fallback: command_prefix:str=','
    command_prefix: str = Field(default=',')
    database_url: str = Field(
        default='postgresql+asyncpg://bot:bot@localhost:5432/junior_atlas'
    )
    redis_url: str = 'redis://localhost:6379/0'
    log_level: str = 'INFO'
    environment: Literal['development', 'staging', 'production'] = 'development'
    guild_id: int | None = Field(default=None, ge=1)
    redis_max_connections: int = Field(default=100, ge=1)
    cache_ttl_seconds: int = Field(default=600, ge=0)
    redis_lock_ttl_ms: int = Field(default=5000, ge=1)
    db_pool_size: int = Field(default=5, ge=0)
    db_max_overflow: int = Field(default=5, ge=0)
    db_use_pgbouncer: bool = False
    db_pool_timeout: float = Field(default=10.0, gt=0)
    db_pool_recycle: int = Field(default=1800, ge=-1)
    db_statement_timeout_ms: int = Field(default=5000, gt=0)
    metrics_host: str = '127.0.0.1'
    metrics_port: int = Field(default=9100, ge=1, le=65535)
    health_port: int = Field(default=8080, ge=1, le=65535)
    dashboard_enabled: bool = False
    dashboard_host: str = '127.0.0.1'
    dashboard_port: int = Field(default=8081, ge=1, le=65535)
    greeting_queue_size: int = Field(default=1000, ge=1)
    greeting_workers: int = Field(default=4, ge=1)
    greeting_max_event_age: float = Field(default=30.0, ge=0)
    invite_join_queue_size: int = Field(default=2000, ge=1)
    invite_stat_flush_interval: float = Field(default=1.0, gt=0)
    shard_count: int | None = Field(default=None, ge=1)
    shard_ids: str = ''
    gateway_queue_size: int = Field(default=4096, ge=1)
    gateway_critical_queue_size: int = Field(default=1024, ge=1)
    gateway_workers: int = Field(default=8, ge=1)
    gateway_guild_concurrency: int = Field(default=1, ge=1)
    gateway_max_event_age: float = Field(default=10.0, ge=0)
    shard_lease_ttl_ms: int = Field(default=60000, ge=1)
    gateway_shutdown_timeout: float = Field(default=15.0, ge=0)
    gateway_dlq_maxsize: int = Field(default=2048, ge=0)
    instance_id: str = Field(default_factory=lambda: os.getenv('HOSTNAME', str(uuid.uuid4())))
    public_base_url: str = 'http://localhost:8080'
    dashboard_api_key: str = ''
    automod_heat_decay: float = Field(default=0.08, ge=0, le=1)
    automod_heat_ttl: int = Field(default=900, ge=1)
    music_url: str = Field(
        default='',
        validation_alias=AliasChoices('LAVALINK_URL', 'music_url'),
    )
    music_password: str = Field(
        default='',
        validation_alias=AliasChoices('LAVALINK_PASSWORD', 'music_password'),
    )
    otel_enabled: bool = False
    otel_exporter_endpoint: str = Field(
        default='',
        validation_alias=AliasChoices(
            'OTEL_EXPORTER_OTLP_ENDPOINT',
            'otel_exporter_endpoint',
        ),
    )
    otel_service_name: str = 'junior-atlas'

    @property
    def token(self) -> str:
        return self.discord_token

    @field_validator('bot_owner_ids', mode='before')
    @classmethod
    def parse_bot_owner_ids(cls, value):
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(',') if item.strip()]
        return value

    @field_validator('bot_owner_ids')
    @classmethod
    def validate_bot_owner_ids(cls, value: list[int]) -> list[int]:
        if any(owner_id <= 0 for owner_id in value):
            raise ValueError('BOT_OWNER_IDS must contain positive Discord IDs')
        return value

    @field_validator('database_url')
    @classmethod
    def normalize_database(cls, value: str) -> str:
        normalized = normalize_database_url(value.strip())
        if not normalized.startswith('postgresql+asyncpg://'):
            raise ValueError(
                'DATABASE_URL must use postgresql+asyncpg:// (or postgresql:// / postgres://, '
                'which are normalized automatically)'
            )
        return normalized

    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith(('redis://', 'rediss://')):
            raise ValueError('REDIS_URL must use redis:// or rediss://')
        return normalized

    @field_validator('guild_id', mode='before')
    @classmethod
    def normalize_guild_id(cls, value):
        if value in (None, '', 0, '0'):
            return None
        return int(value)

    @field_validator('log_level')
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper().strip()
        if normalized not in {'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'}:
            raise ValueError('LOG_LEVEL must be one of CRITICAL, ERROR, WARNING, INFO, DEBUG')
        return normalized

    @field_validator('command_prefix')
    @classmethod
    def validate_command_prefix(cls, value: str) -> str:
        prefix = value.strip()
        if not prefix or len(prefix) > 5 or any(char.isspace() for char in prefix):
            raise ValueError('COMMAND_PREFIX must be 1-5 characters with no whitespace')
        return prefix

    @field_validator('shard_count', mode='before')
    @classmethod
    def normalize_optional_shard_count(cls, value):
        if value in (None, '', 0, '0'):
            return None
        return int(value)

    @field_validator('instance_id', mode='before')
    @classmethod
    def default_instance_id(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return os.getenv('HOSTNAME') or str(uuid.uuid4())
        return value

    @field_validator('instance_id')
    @classmethod
    def validate_instance_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('INSTANCE_ID must not be empty')
        return value.strip()

    @field_validator('otel_service_name')
    @classmethod
    def validate_otel_service_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('OTEL_SERVICE_NAME must not be empty')
        return value.strip()

    @model_validator(mode='after')
    def validate_queue_capacity(self):
        if self.gateway_critical_queue_size > self.gateway_queue_size:
            raise ValueError(
                'GATEWAY_CRITICAL_QUEUE_SIZE cannot exceed GATEWAY_QUEUE_SIZE'
            )
        return self

    @property
    def parsed_shard_ids(self):
        raw = self.shard_ids.strip()
        if not raw:
            return None
        parts = raw.split(',')
        if any(not part.strip() for part in parts):
            raise ValueError("SHARD_IDS must be comma-separated integers without empty entries")
        try:
            shard_ids = [int(part.strip()) for part in parts]
        except ValueError as exc:
            raise ValueError("SHARD_IDS must contain only integer IDs, for example '0,1'") from exc
        if any(shard_id < 0 for shard_id in shard_ids):
            raise ValueError("SHARD_IDS cannot contain negative IDs")
        if len(set(shard_ids)) != len(shard_ids):
            raise ValueError("SHARD_IDS cannot contain duplicate IDs")
        if self.shard_count is not None and any(shard_id >= self.shard_count for shard_id in shard_ids):
            raise ValueError("Every SHARD_IDS entry must be smaller than SHARD_COUNT")
        return shard_ids


def validate_startup(settings: Settings) -> None:
    """Reject configurations that cannot produce a usable bot session.

    Raise a single actionable error instead of letting discord.py fail later
    with an opaque ``LoginFailure`` (which also risks echoing malformed input).
    """
    if not settings.discord_token or not settings.discord_token.strip():
        raise ConfigurationError(
            'DISCORD_TOKEN is not set. Copy .env.example to .env and set a valid '
            'Discord bot token, or provide DISCORD_TOKEN in the process environment.'
        )
    # Accessing the property validates SHARD_IDS before connecting to Discord.
    _ = settings.parsed_shard_ids


def log_startup_error(error: ConfigurationError) -> None:
    logging.getLogger('bot').error('Startup configuration error: %s', error)


settings=Settings()

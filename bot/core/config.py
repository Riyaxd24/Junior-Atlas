from __future__ import annotations

import os
import uuid
from math import isfinite
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, field_validator
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
        default='postgresql+asyncpg://bot:bot@localhost:5432/discordbot'
    )
    redis_url: str = 'redis://localhost:6379/0'
    log_level: str = 'INFO'
    environment: Literal['development', 'staging', 'production'] = 'development'
    guild_id: int | None = None
    redis_max_connections: int = 100
    cache_ttl_seconds: int = 600
    redis_lock_ttl_ms: int = 5000
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_use_pgbouncer: bool = False
    db_pool_timeout: float = 10.0
    db_pool_recycle: int = 1800
    db_statement_timeout_ms: int = 5000
    metrics_host: str = '127.0.0.1'
    metrics_port: int = 9100
    health_port: int = 8080
    dashboard_host: str = '127.0.0.1'
    dashboard_port: int = 8081
    greeting_queue_size: int = 1000
    greeting_workers: int = 4
    greeting_max_event_age: float = 30.0
    invite_join_queue_size: int = 2000
    invite_stat_flush_interval: float = 1.0
    shard_count: int | None = None
    shard_ids: str = ''
    gateway_queue_size: int = 4096
    gateway_critical_queue_size: int = 1024
    gateway_workers: int = 8
    gateway_guild_concurrency: int = 1
    gateway_max_event_age: float = 10.0
    shard_lease_ttl_ms: int = 60000
    gateway_shutdown_timeout: float = 15.0
    gateway_dlq_maxsize: int = 2048
    instance_id: str = Field(default_factory=lambda: os.getenv('HOSTNAME', str(uuid.uuid4())))
    public_base_url: str = 'http://localhost:8080'
    dashboard_api_key: str = ''
    automod_heat_decay: float = 0.08
    automod_heat_ttl: int = 900
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
    otel_service_name: str = 'junior-atlas-bot'

    @property
    def token(self) -> str:
        return self.discord_token

    @field_validator('bot_owner_ids', mode='before')
    @classmethod
    def parse_bot_owner_ids(cls, value):
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(',') if item.strip()]
        return value

    @field_validator('database_url')
    @classmethod
    def normalize_database(cls, value: str) -> str:
        return normalize_database_url(value)

    @field_validator('guild_id', mode='before')
    @classmethod
    def normalize_guild_id(cls, value):
        if value in (None, '', 0, '0'):
            return None
        return int(value)

    @field_validator('log_level')
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator('command_prefix')
    @classmethod
    def validate_command_prefix(cls, value: str) -> str:
        prefix = value.strip()
        if not prefix or len(prefix) > 5 or any(char.isspace() for char in prefix):
            raise ValueError('COMMAND_PREFIX must be 1-5 characters with no whitespace')
        return prefix
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

settings=Settings()

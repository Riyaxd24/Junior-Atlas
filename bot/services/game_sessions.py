"""Active game state storage for restart-safe interactive games.

Only live engines are stored. The in-memory mapping makes normal play fast;
when Redis is available the serialized engine is also written with a TTL so a
newly started process can resume the match with ``/uno resume`` or
``/handcricket resume``.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

GAME_TTL_SECONDS = 60 * 60 * 6


class GameStore:
    def __init__(self, cache=None):
        self.cache = cache
        self.active: dict[tuple[int, int, str], object] = {}

    @staticmethod
    def key(guild_id: int, channel_id: int, kind: str) -> tuple[int, int, str]:
        return (int(guild_id), int(channel_id), str(kind))

    def get(self, guild_id: int, channel_id: int, kind: str):
        return self.active.get(self.key(guild_id, channel_id, kind))

    async def save(self, guild_id: int, channel_id: int, kind: str, engine) -> None:
        self.active[self.key(guild_id, channel_id, kind)] = engine
        client = getattr(self.cache, "client", None)
        if client is None:
            return
        try:
            payload = json.dumps(engine.to_dict(), separators=(",", ":"))
            await client.set(self._redis_key(guild_id, channel_id, kind), payload, ex=GAME_TTL_SECONDS)
        except Exception:
            log.warning(
                "could not persist game state guild=%s channel=%s kind=%s",
                guild_id,
                channel_id,
                kind,
                exc_info=True,
            )

    async def load(self, guild_id: int, channel_id: int, kind: str):
        key = self.key(guild_id, channel_id, kind)
        engine = self.active.get(key)
        if engine is not None:
            return engine
        client = getattr(self.cache, "client", None)
        if client is None:
            return None
        try:
            payload = await client.get(self._redis_key(guild_id, channel_id, kind))
        except Exception:
            log.warning(
                "could not load game state guild=%s channel=%s kind=%s",
                guild_id,
                channel_id,
                kind,
                exc_info=True,
            )
            return None
        if not payload:
            return None
        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            log.warning("corrupt game state guild=%s channel=%s kind=%s", guild_id, channel_id, kind)
            return None
        return data

    async def load_engine(self, guild_id: int, channel_id: int, kind: str, factory):
        """Load a live engine, rebuilding it with ``factory`` after a restart."""
        value = await self.load(guild_id, channel_id, kind)
        if value is None:
            return None
        if isinstance(value, dict):
            try:
                value = factory(value)
            except (KeyError, TypeError, ValueError):
                log.warning(
                    "could not rebuild game state guild=%s channel=%s kind=%s",
                    guild_id,
                    channel_id,
                    kind,
                    exc_info=True,
                )
                await self.clear(guild_id, channel_id, kind)
                return None
            self.active[self.key(guild_id, channel_id, kind)] = value
        return value

    async def clear(self, guild_id: int, channel_id: int, kind: str) -> None:
        self.active.pop(self.key(guild_id, channel_id, kind), None)
        client = getattr(self.cache, "client", None)
        if client is None:
            return
        try:
            await client.delete(self._redis_key(guild_id, channel_id, kind))
        except Exception:
            log.warning(
                "could not clear game state guild=%s channel=%s kind=%s",
                guild_id,
                channel_id,
                kind,
                exc_info=True,
            )

    @staticmethod
    def _redis_key(guild_id: int, channel_id: int, kind: str) -> str:
        return f"game-session:{kind}:{guild_id}:{channel_id}"

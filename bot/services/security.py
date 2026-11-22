from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic
from typing import ClassVar


class AntiNukeService:
    DEFAULTS: ClassVar[dict[str, dict[str, float]]] = {
        "channel_delete": {"threshold": 3, "window": 30.0, "confidence": 0.90},
        "role_delete": {"threshold": 3, "window": 30.0, "confidence": 0.90},
        "channel_create": {"threshold": 5, "window": 30.0, "confidence": 0.95},
        "role_create": {"threshold": 5, "window": 30.0, "confidence": 0.95},
        "ban": {"threshold": 3, "window": 60.0, "confidence": 0.95},
        "kick": {"threshold": 5, "window": 60.0, "confidence": 0.95},
        "join": {"threshold": 8, "window": 10.0, "confidence": 0.90},
        "webhook": {"threshold": 3, "window": 60.0, "confidence": 0.95},
        "admin_role_change": {"threshold": 2, "window": 60.0, "confidence": 0.95},
    }

    def __init__(self):
        self._windows: dict[tuple[int, int, str], deque[float]] = defaultdict(deque)

    def assess(self, event_type, count, confidence):
        policy = self.DEFAULTS[event_type]
        threshold = int(policy["threshold"])
        required_confidence = float(policy["confidence"])
        should_alert = count >= 1
        should_act = (
            count >= threshold
            and float(confidence) >= required_confidence
        )
        return {
            "alert": should_alert,
            "automate": should_act,
            "threshold": threshold,
            "confidence": float(confidence),
        }

    def observe(self, guild_id, actor_id, event_type, confidence=1.0):
        policy = self.DEFAULTS[event_type]
        now = monotonic()
        key = (guild_id, actor_id, event_type)
        window = float(policy["window"])
        queue = self._windows[key]
        while queue and now - queue[0] > window:
            queue.popleft()
        queue.append(now)
        return self.assess(event_type, len(queue), confidence)

    @staticmethod
    def trusted(member):
        guild = member.guild
        if member.id == guild.owner_id:
            return True
        permissions = member.guild_permissions
        return bool(permissions.administrator)

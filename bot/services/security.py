"""Anti-nuke detection policy and attribution-safe throttling.

The service is deliberately pure/in-memory: Discord objects are resolved by the
bot, persistence is owned by :class:`~bot.services.extreme.ExtremeService`, and
only confirmed state changes are reported as successful.
"""
from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from time import monotonic
from typing import ClassVar

# Actions an administrator can tune through ``/security config``.
SECURITY_ACTIONS = (
    "channel_delete",
    "role_delete",
    "channel_create",
    "role_create",
    "ban",
    "kick",
    "join",
    "webhook",
    "admin_role_change",
    "permission_change",
)

DEFAULT_SECURITY_SETTINGS: dict = {
    "enabled": True,
    "quarantine_enabled": True,
    "recovery_enabled": True,
    "notify_channel_id": None,
    "trusted_user_ids": [],
    "punishment": "quarantine",  # quarantine | lockdown | none
    "thresholds": {
        "channel_delete": {"threshold": 3, "window_seconds": 30},
        "role_delete": {"threshold": 3, "window_seconds": 30},
        "channel_create": {"threshold": 5, "window_seconds": 30},
        "role_create": {"threshold": 5, "window_seconds": 30},
        "ban": {"threshold": 3, "window_seconds": 60},
        "kick": {"threshold": 5, "window_seconds": 60},
        "webhook": {"threshold": 3, "window_seconds": 60},
        "admin_role_change": {"threshold": 2, "window_seconds": 60},
        "permission_change": {"threshold": 3, "window_seconds": 60},
    },
    "raid": {
        "enabled": False,
        "join_threshold": 8,
        "window_seconds": 10,
        "min_account_age_days": 7,
        "quarantine_new_accounts": True,
        "lockdown": True,
    },
}


def normalize_security_settings(raw) -> dict:
    """Merge stored settings with defaults and discard malformed values."""
    settings = deepcopy(DEFAULT_SECURITY_SETTINGS)
    if not isinstance(raw, dict):
        return settings

    for key in ("enabled", "quarantine_enabled", "recovery_enabled"):
        if isinstance(raw.get(key), bool):
            settings[key] = raw[key]
    if isinstance(raw.get("notify_channel_id"), int) and raw["notify_channel_id"] > 0:
        settings["notify_channel_id"] = raw["notify_channel_id"]
    if isinstance(raw.get("punishment"), str) and raw["punishment"] in {
        "quarantine",
        "lockdown",
        "none",
    }:
        settings["punishment"] = raw["punishment"]
    trusted = raw.get("trusted_user_ids")
    if isinstance(trusted, list):
        settings["trusted_user_ids"] = sorted(
            {
                int(value)
                for value in trusted
                if isinstance(value, int) and value > 0
            }
        )

    thresholds = raw.get("thresholds")
    if isinstance(thresholds, dict):
        for action, policy in thresholds.items():
            if action not in settings["thresholds"] or not isinstance(policy, dict):
                continue
            current = settings["thresholds"][action]
            threshold = policy.get("threshold")
            window = policy.get("window_seconds")
            if isinstance(threshold, int) and 1 <= threshold <= 100:
                current["threshold"] = threshold
            if isinstance(window, int) and 1 <= window <= 3600:
                current["window_seconds"] = window

    raid = raw.get("raid")
    if isinstance(raid, dict):
        for key in ("enabled", "quarantine_new_accounts", "lockdown"):
            if isinstance(raid.get(key), bool):
                settings["raid"][key] = raid[key]
        for key, low, high in (
            ("join_threshold", 2, 100),
            ("window_seconds", 1, 600),
            ("min_account_age_days", 0, 365),
        ):
            value = raid.get(key)
            if isinstance(value, int) and low <= value <= high:
                settings["raid"][key] = value
    return settings


def merge_security_updates(settings: dict, **changes) -> dict:
    """Validate and apply an administrator update to a settings snapshot."""
    updated = deepcopy(normalize_security_settings(settings))

    if "enabled" in changes and changes["enabled"] is not None:
        updated["enabled"] = bool(changes["enabled"])
    if "quarantine_enabled" in changes and changes["quarantine_enabled"] is not None:
        updated["quarantine_enabled"] = bool(changes["quarantine_enabled"])
    if "recovery_enabled" in changes and changes["recovery_enabled"] is not None:
        updated["recovery_enabled"] = bool(changes["recovery_enabled"])
    if "punishment" in changes and changes["punishment"] is not None:
        punishment = str(changes["punishment"]).lower()
        if punishment not in {"quarantine", "lockdown", "none"}:
            raise ValueError("punishment must be quarantine, lockdown, or none")
        updated["punishment"] = punishment

    if changes.get("notify_channel_id") is not None:
        value = int(changes["notify_channel_id"])
        if value <= 0:
            raise ValueError("notify channel id must be positive")
        updated["notify_channel_id"] = value
    if changes.get("clear_notify_channel"):
        updated["notify_channel_id"] = None

    trusted_add = changes.get("trusted_add")
    if trusted_add is not None:
        value = int(trusted_add)
        if value <= 0:
            raise ValueError("trusted user id must be positive")
        updated["trusted_user_ids"] = sorted(set(updated["trusted_user_ids"]) | {value})
    trusted_remove = changes.get("trusted_remove")
    if trusted_remove is not None:
        value = int(trusted_remove)
        updated["trusted_user_ids"] = sorted(
            set(updated["trusted_user_ids"]) - {value}
        )

    action = changes.get("action")
    if action is not None:
        if action not in SECURITY_ACTIONS:
            raise ValueError(f"unknown security action: {action}")
        if changes.get("threshold") is not None:
            threshold = int(changes["threshold"])
            if not 1 <= threshold <= 100:
                raise ValueError("threshold must be between 1 and 100")
            updated["thresholds"][action]["threshold"] = threshold
        if changes.get("window_seconds") is not None:
            window = int(changes["window_seconds"])
            if not 1 <= window <= 3600:
                raise ValueError("window_seconds must be between 1 and 3600")
            updated["thresholds"][action]["window_seconds"] = window

    if changes.get("raid") is not None:
        raid_changes = changes["raid"]
        if not isinstance(raid_changes, dict):
            raise ValueError("raid settings must be a mapping")
        for key in ("enabled", "quarantine_new_accounts", "lockdown"):
            if key in raid_changes and raid_changes[key] is not None:
                updated["raid"][key] = bool(raid_changes[key])
        bounds = {
            "join_threshold": (2, 100),
            "window_seconds": (1, 600),
            "min_account_age_days": (0, 365),
        }
        for key, (low, high) in bounds.items():
            if key in raid_changes and raid_changes[key] is not None:
                value = int(raid_changes[key])
                if not low <= value <= high:
                    raise ValueError(f"raid {key} must be between {low} and {high}")
                updated["raid"][key] = value
    return updated


class AntiNukeService:
    # Kept for backward compatibility with callers/tests that expect DEFAULTS.
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
        "permission_change": {"threshold": 3, "window": 60.0, "confidence": 0.95},
    }

    def __init__(self):
        self._windows: dict[tuple[int, int, str], deque[float]] = defaultdict(deque)

    @classmethod
    def policy_for(cls, settings: dict | None, event_type: str) -> dict:
        configured = (settings or {}).get("thresholds", {}).get(event_type)
        default = cls.DEFAULTS[event_type]
        if not isinstance(configured, dict):
            configured = {}
        return {
            "threshold": int(configured.get("threshold", default["threshold"])),
            "window": float(configured.get("window_seconds", default["window"])),
            "confidence": float(default["confidence"]),
        }

    def assess(self, event_type, count, confidence, policy=None):
        policy = policy or self.DEFAULTS[event_type]
        threshold = int(policy["threshold"])
        required_confidence = float(policy["confidence"])
        should_act = count >= threshold and float(confidence) >= required_confidence
        return {
            "alert": count >= 1,
            "automate": should_act,
            "threshold": threshold,
            "confidence": float(confidence),
        }

    def observe(self, guild_id, actor_id, event_type, confidence=1.0, policy=None):
        policy = policy or self.policy_for(None, event_type)
        now = monotonic()
        key = (guild_id, actor_id, event_type)
        window = float(policy["window"])
        queue = self._windows[key]
        while queue and now - queue[0] > window:
            queue.popleft()
        queue.append(now)
        return self.assess(event_type, len(queue), confidence, policy)

    def burst_count(self, guild_id, actor_id, event_type) -> int:
        return len(self._windows.get((guild_id, actor_id, event_type), ()))

    def clear(self, guild_id, actor_id, event_type: str | None = None) -> None:
        if event_type is None:
            for key in list(self._windows):
                if key[0] == guild_id and key[1] == actor_id:
                    self._windows.pop(key, None)
            return
        self._windows.pop((guild_id, actor_id, event_type), None)

    @staticmethod
    def trusted(member, trusted_ids=()) -> bool:
        """Return True for the owner, administrators and explicit allowlists."""
        guild = getattr(member, "guild", None)
        if member is None or guild is None:
            return False
        if int(getattr(member, "id", 0)) == getattr(guild, "owner_id", None):
            return True
        if int(getattr(member, "id", 0)) in set(trusted_ids or ()):
            return True
        permissions = getattr(member, "guild_permissions", None)
        return bool(getattr(permissions, "administrator", False))

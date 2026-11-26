from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from collections import defaultdict, deque
from time import monotonic
from typing import NamedTuple
from urllib.parse import urlparse

import discord

from bot.models import AutoModLog
from bot.repositories.automod import AutoModRepository

RULE_TYPES = (
    "spam",
    "repeated",
    "mentions",
    "invites",
    "blocked_words",
    "links",
    "emoji",
    "caps",
    "length",
)
RULE_ACTIONS = ("delete", "warn", "timeout", "kick")
ESCALATION_ACTIONS = ("warn", "timeout", "kick")
INVITE_RE = re.compile(
    r"(?:https?://)?(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite)/[a-zA-Z0-9]+",
    re.IGNORECASE,
)
LINK_RE = re.compile(
    r"(?:https?://|www\.)(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?",
    re.IGNORECASE,
)
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")

log = logging.getLogger(__name__)


class Violation(NamedTuple):
    rule_type: str
    action: str
    reason: str
    duration_seconds: int | None = None


class AutoModService:
    def __init__(self, db, cache=None):
        self.repository = AutoModRepository(db)
        self.cache = cache
        self._windows = defaultdict(deque)

    async def rules(self, guild_id):
        """Return persisted AutoMod rules for a guild."""
        return await self.repository.get_rules(guild_id)

    async def configure_rule(
        self,
        guild_id,
        rule_type,
        *,
        enabled,
        threshold,
        action,
        duration_seconds=300,
        exempt_roles=None,
        exempt_channels=None,
        custom_data=None,
    ):
        self._validate_rule_type(rule_type)
        if threshold < 1 or threshold > 100000:
            raise ValueError("Threshold must be between 1 and 100000.")
        if action not in RULE_ACTIONS:
            raise ValueError("Unsupported AutoMod action.")
        if action == "timeout" and not 1 <= duration_seconds <= 2419200:
            raise ValueError("Timeout duration must be between 1 and 2419200 seconds.")
        await self.repository.configure_rule(
            guild_id,
            rule_type,
            enabled=enabled,
            threshold=threshold,
            action=action,
            duration_seconds=duration_seconds,
            exempt_roles=exempt_roles,
            exempt_channels=exempt_channels,
            custom_data=custom_data,
        )

    async def set_exemption(
        self,
        guild_id,
        rule_type,
        *,
        value,
        channel,
        exempt,
    ):
        self._validate_rule_type(rule_type)
        rules = await self.repository.get_rules(guild_id)
        rule = next((row for row in rules if row.name == rule_type), None)
        config = dict(rule.config) if rule is not None else {}
        key = "exempt_channels" if channel else "exempt_roles"
        values = set(config.get(key, []))
        if exempt:
            values.add(value)
        else:
            values.discard(value)
        config[key] = sorted(values)
        await self.repository.configure_rule(
            guild_id,
            rule_type,
            enabled=bool(rule.enabled) if rule is not None else False,
            threshold=config.get("threshold", 5),
            action=rule.action if rule is not None else "delete",
            duration_seconds=config.get("duration_seconds", 300),
            exempt_roles=config.get("exempt_roles", []),
            exempt_channels=config.get("exempt_channels", []),
            custom_data=config,
        )

    async def inspect_message(self, message):
        if (
            message.author.bot
            or message.guild is None
            or not isinstance(message.author, discord.Member)
        ):
            return None
        member = message.author
        guild = message.guild
        if member.id == guild.owner_id or guild.me is None:
            return None
        if member.top_role >= guild.me.top_role:
            return None
        permissions = member.guild_permissions
        if (
            permissions.administrator
            or permissions.manage_guild
            or permissions.manage_messages
        ):
            return None

        rules = await self.repository.get_rules(guild.id)
        role_ids = {role.id for role in member.roles}
        for rule in rules:
            if not rule.enabled or rule.kind != "filter":
                continue
            config = dict(rule.config or {})
            if role_ids.intersection(config.get("exempt_roles", [])):
                continue
            if message.channel.id in config.get("exempt_channels", []):
                continue
            violation = await self._check_rule(message, rule.name, rule, config)
            if violation is None:
                continue
            action = rule.action
            duration = config.get("duration_seconds")
            escalation = await self._escalated_action(
                guild.id,
                member.id,
                rule.name,
                config,
            )
            if escalation is not None:
                action, duration = escalation
            await self.repository.add_log(
                AutoModLog(
                    guild_id=guild.id,
                    user_id=member.id,
                    rule_type=rule.name,
                    action_taken=action,
                    channel_id=message.channel.id,
                    message_content=None,
                )
            )
            return Violation(rule.name, action, violation.reason, duration)
        return None

    async def _check_rule(self, message, rule_type, rule=None, config=None):
        config = config or {}
        content = message.content or ""
        threshold = int(config.get("threshold", 5))

        if rule_type == "spam":
            count = await self._record_event(
                message,
                rule_type,
                content,
                window_seconds=5,
            )
            if count > threshold:
                return Violation(rule_type, "delete", "Rapid repeated messages detected.")
        elif rule_type == "repeated":
            count = await self._record_event(
                message,
                rule_type,
                content,
                window_seconds=60,
            )
            if count >= threshold:
                return Violation(rule_type, "delete", "Repeated message detected.")
        elif rule_type == "mentions":
            mention_count = len(getattr(message, "mentions", []))
            mention_count += len(getattr(message, "role_mentions", []))
            # ``@everyone`` and ``@here`` do not appear in ``mentions`` or
            # ``role_mentions``, but they are the highest-impact pings and must
            # count toward mass-mention protection.
            if getattr(message, "mention_everyone", False):
                mention_count += 1
            if mention_count >= threshold:
                return Violation(rule_type, "delete", "Mention spam detected.")
        elif rule_type == "invites":
            if INVITE_RE.search(content):
                return Violation(rule_type, "delete", "Discord invite link detected.")
        elif rule_type == "blocked_words":
            words = config.get("words", [])
            folded = content.casefold()
            if any(re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", folded) for word in words):
                return Violation(rule_type, "delete", "Blocked word detected.")
        elif rule_type == "links":
            deny_domains = set(config.get("deny_domains", []))
            allow_domains = set(config.get("allow_domains", []))
            for match in LINK_RE.findall(content):
                domain = urlparse(match if "://" in match else f"//{match}").hostname or ""
                domain = domain.lower().rstrip(".")
                if domain in allow_domains:
                    continue
                if deny_domains and any(
                    domain == denied or domain.endswith(f".{denied}")
                    for denied in deny_domains
                ):
                    return Violation(rule_type, "delete", "Denied link domain detected.")
        elif rule_type == "emoji":
            if len(EMOJI_RE.findall(content)) >= threshold:
                return Violation(rule_type, "delete", "Emoji spam detected.")
        elif rule_type == "caps":
            letters = [char for char in content if char.isalpha()]
            if len(letters) >= 5:
                uppercase = sum(char.isupper() for char in letters)
                if uppercase / len(letters) * 100 >= threshold:
                    return Violation(rule_type, "delete", "Excessive capitalization detected.")
        elif rule_type == "length" and len(content) > threshold:
            return Violation(rule_type, "delete", "Message length limit exceeded.")
        return None

    async def configure_word(self, guild_id, word, enabled):
        normalized = word.strip().casefold()
        if not normalized or len(normalized) > 80:
            raise ValueError("Blocked words must contain 1 to 80 characters.")
        rules = await self.repository.get_rules(guild_id)
        rule = next((row for row in rules if row.name == "blocked_words"), None)
        config = dict(rule.config) if rule is not None else {}
        words = set(config.get("words", []))
        if enabled:
            words.add(normalized)
        else:
            words.discard(normalized)
        config["words"] = sorted(words)
        await self.repository.configure_rule(
            guild_id,
            "blocked_words",
            enabled=bool(rule.enabled) if rule is not None else False,
            threshold=config.get("threshold", 5),
            action=rule.action if rule is not None else "delete",
            duration_seconds=config.get("duration_seconds", 300),
            custom_data=config,
        )

    async def configure_link_domain(self, guild_id, domain, mode, enabled):
        normalized = domain.strip().lower().rstrip(".")
        if mode not in {"allow", "deny"} or not normalized:
            raise ValueError("Link mode must be allow or deny with a valid domain.")
        rules = await self.repository.get_rules(guild_id)
        rule = next((row for row in rules if row.name == "links"), None)
        config = dict(rule.config) if rule is not None else {}
        key = f"{mode}_domains"
        domains = set(config.get(key, []))
        if enabled:
            domains.add(normalized)
        else:
            domains.discard(normalized)
        config[key] = sorted(domains)
        await self.repository.configure_rule(
            guild_id,
            "links",
            enabled=bool(rule.enabled) if rule is not None else False,
            threshold=config.get("threshold", 5),
            action=rule.action if rule is not None else "delete",
            duration_seconds=config.get("duration_seconds", 300),
            custom_data=config,
        )

    async def set_escalation(
        self,
        guild_id,
        rule_type,
        *,
        threshold,
        action,
        duration_seconds,
        enabled,
        window_seconds,
    ):
        self._validate_rule_type(rule_type)
        if threshold < 1:
            raise ValueError("Escalation threshold must be at least one.")
        if action not in ESCALATION_ACTIONS:
            raise ValueError("Escalation action must be warn, timeout, or kick.")
        if not 60 <= window_seconds <= 2678400:
            raise ValueError("Escalation window must be between 1 minute and 31 days.")
        rules = await self.repository.get_rules(guild_id)
        rule = next((row for row in rules if row.name == rule_type), None)
        config = dict(rule.config) if rule is not None else {}
        steps = {
            step["threshold"]: step
            for step in config.get("escalation", [])
            if isinstance(step, dict) and "threshold" in step
        }
        if enabled:
            steps[threshold] = {
                "threshold": threshold,
                "action": action,
                "duration_seconds": duration_seconds if action == "timeout" else None,
            }
        else:
            steps.pop(threshold, None)
        config["escalation"] = [steps[key] for key in sorted(steps)]
        config["escalation_window_seconds"] = window_seconds
        await self.repository.configure_rule(
            guild_id,
            rule_type,
            enabled=bool(rule.enabled) if rule is not None else False,
            threshold=config.get("threshold", 5),
            action=rule.action if rule is not None else "delete",
            duration_seconds=config.get("duration_seconds", 300),
            custom_data=config,
        )

    async def _escalated_action(self, guild_id, user_id, rule_type, config):
        steps = config.get("escalation", [])
        if not steps:
            return None
        window_seconds = int(config.get("escalation_window_seconds", 604800))
        count = await self.repository.count_recent_violations(
            guild_id,
            user_id,
            rule_type,
            window_seconds,
        )
        selected = None
        for step in sorted(steps, key=lambda item: item["threshold"]):
            if count >= int(step["threshold"]):
                selected = step
        if selected is None:
            return None
        return selected["action"], selected.get("duration_seconds")

    async def _record_event(self, message, rule_type, content, window_seconds):
        """Record one event and return the count inside the sliding window.

        Redis is authoritative when reachable so every shard/process shares the
        same counter. The local deque is a bounded fallback for tests and
        deployments without Redis; it is never mixed with the Redis count.
        """
        # The repeated-message rule is per content hash, while spam is per user.
        bucket = "all"
        if rule_type == "repeated":
            bucket = hashlib.sha256((content or "").casefold().encode()).hexdigest()[:20]

        if self.cache is not None and getattr(self.cache, "client", None) is not None:
            key = f"automod:events:{message.guild.id}:{message.author.id}:{rule_type}:{bucket}"
            now = time.time()
            member = f"{now}:{uuid.uuid4().hex}"
            script = (
                "local k=KEYS[1]; local now=tonumber(ARGV[1]); "
                "local window=tonumber(ARGV[2]); "
                "redis.call('ZREMRANGEBYSCORE',k,0,now-window); "
                "redis.call('ZADD',k,now,ARGV[3]); "
                "redis.call('EXPIRE',k,window+2); "
                "return redis.call('ZCARD',k)"
            )
            try:
                count = await self.cache.client.eval(
                    script, 1, key, now, window_seconds, member
                )
                return int(count)
            except Exception:
                log.warning(
                    "automod Redis window failed guild=%s user=%s; using local fallback",
                    message.guild.id,
                    message.author.id,
                    exc_info=True,
                )

        local_key = (message.guild.id, message.author.id, rule_type, bucket)
        now = monotonic()
        queue = self._windows[local_key]
        while queue and now - queue[0] > window_seconds:
            queue.popleft()
        queue.append(now)
        return len(queue)

    @staticmethod
    def _validate_rule_type(rule_type):
        if rule_type not in RULE_TYPES:
            raise ValueError("Unsupported AutoMod rule type.")

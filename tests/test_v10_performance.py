from pathlib import Path


def test_prefix_commands_have_fast_lane_before_heavy_message_work():
    src = Path('bot/core/bot.py').read_text()
    # Prefix matching must resolve the callable command_prefix rather than
    # calling str.startswith on it (which raises TypeError).
    fast = src.index('prefix = match_message_prefix(')
    cfg = src.index('cfg=await self.guild_config.get(message.guild.id)', fast)
    invoke = src.index('await self.invoke(ctx)', fast)
    assert invoke < cfg


def test_release_name_is_v10():
    src = Path('scripts/build_release.py').read_text()
    assert 'junior-atlas-0.1.0.zip' in src

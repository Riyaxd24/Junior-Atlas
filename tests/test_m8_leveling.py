from bot.services.levels import LevelService


def test_level_threshold_progression_is_monotonic():
    previous = 0
    for level in range(LevelService.MAX_LEVEL + 1):
        threshold = LevelService.xp_needed(level)
        assert threshold >= previous
        previous = threshold
        assert LevelService.level_from_total_xp(threshold) >= level


def test_level_from_total_xp_matches_threshold_boundaries():
    assert LevelService.level_from_total_xp(0) == 0
    assert LevelService.level_from_total_xp(99) == 0
    assert LevelService.level_from_total_xp(100) == 1
    assert LevelService.level_from_total_xp(254) == 1
    assert LevelService.level_from_total_xp(255) == 2


def test_character_xp_counts_letters_only():
    assert LevelService.character_count("Hi 123!") == 2

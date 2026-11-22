from bot.models.community import CollectibleItem, TempVoiceSetting


def test_collectible_model_is_guild_scoped():
    collectible = CollectibleItem(
        guild_id=1,
        name="Blue Star",
        category="badge",
        rarity="rare",
        description="A test collectible",
        emoji="🌟",
    )
    assert collectible.guild_id == 1
    assert collectible.rarity == "rare"


def test_temp_voice_setting_validates_name_format():
    setting = TempVoiceSetting(
        guild_id=1,
        hub_channel_id=2,
        category_id=3,
        default_name="{user}'s Channel",
        user_limit=4,
    )
    assert setting.default_name.format(user="Ada") == "Ada's Channel"
    assert setting.user_limit == 4

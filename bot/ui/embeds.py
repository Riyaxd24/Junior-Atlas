import discord

COLOURS = {
    'primary': discord.Colour(0x5865F2),
    'dark': discord.Colour(0x202225),
    'surface': discord.Colour(0x2B2D31),
    'success': discord.Colour(0x3BA55D),
    'warning': discord.Colour(0xFAA61A),
    'error': discord.Colour(0xED4245),
    'text': discord.Colour(0xF2F3F5),
    'info': discord.Colour(0x5865F2),
    'moderation': discord.Colour.from_rgb(237, 93, 93),
    'security': discord.Colour.from_rgb(170, 62, 255),
}


def _base(title: str, description: str, kind: str = 'info') -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        colour=COLOURS.get(kind, COLOURS['info']),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text='Junior Atlas')
    return embed


def success_embed(title: str, description: str) -> discord.Embed:
    return _base(f'✓ {title}', description, 'success')


def error_embed(title: str, description: str) -> discord.Embed:
    return _base(f'✕ {title}', description, 'error')


def warning_embed(title: str, description: str) -> discord.Embed:
    return _base(f'⚠ {title}', description, 'warning')


def info_embed(title: str, description: str, *, thumbnail: str | None = None) -> discord.Embed:
    embed = _base(title, description, 'info')
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed


def command_embed(title: str, description: str, *, kind: str = 'info', thumbnail: str | None = None) -> discord.Embed:
    embed = _base(title, description, kind)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed

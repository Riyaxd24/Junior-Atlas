"""Original, locally rendered pixel-art cards for interaction embeds.

These cards are drawn with Pillow at runtime.  They are deliberately simple,
blocky and Minecraft-inspired, and they never require an external image host.
If rendering fails for any reason the caller receives ``None`` and the embed
simply falls back to text-only presentation.
"""
from __future__ import annotations

import io
import logging
from functools import lru_cache

log = logging.getLogger("bot.pixel_art")

CARD_WIDTH = 480
CARD_HEIGHT = 160

_SKIN = (222, 184, 135)
_HAIR = (64, 42, 28)
_PANTS = (60, 80, 160)
_LEATHER = (139, 90, 43)
_STONE = (128, 128, 128)
_IRON = (210, 210, 215)
_WATER = (47, 111, 235)
_LEAF = (56, 145, 58)
_WOOD = (160, 110, 60)
_GOLD = (242, 201, 76)
_RED = (220, 60, 60)
_WHITE = (245, 245, 245)


def _rgb(value: int) -> tuple[int, int, int]:
    value = int(value) & 0xFFFFFF
    return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


def _font(size: int):
    from PIL import ImageFont

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _draw_character(draw, x: int, y: int, shirt: tuple[int, int, int]) -> None:
    """Draw a blocky two-tone character with a tiny pixel face."""
    draw.rectangle([x + 10, y, x + 42, y + 30], fill=_SKIN, outline=(80, 55, 35))
    draw.rectangle([x + 10, y, x + 42, y + 8], fill=_HAIR)
    draw.rectangle([x + 18, y + 14, x + 22, y + 18], fill=(30, 30, 30))
    draw.rectangle([x + 30, y + 14, x + 34, y + 18], fill=(30, 30, 30))
    draw.rectangle([x + 22, y + 23, x + 31, y + 25], fill=(120, 70, 55))
    draw.rectangle([x + 8, y + 31, x + 44, y + 68], fill=shirt, outline=(35, 35, 35))
    draw.rectangle([x, y + 34, x + 8, y + 62], fill=shirt, outline=(35, 35, 35))
    draw.rectangle([x + 44, y + 34, x + 52, y + 62], fill=shirt, outline=(35, 35, 35))
    draw.rectangle([x + 8, y + 69, x + 24, y + 94], fill=_PANTS, outline=(30, 30, 50))
    draw.rectangle([x + 28, y + 69, x + 44, y + 94], fill=_PANTS, outline=(30, 30, 50))
    draw.rectangle([x + 6, y + 95, x + 24, y + 100], fill=(50, 50, 55))
    draw.rectangle([x + 28, y + 95, x + 46, y + 100], fill=(50, 50, 55))


def _draw_heart(draw, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    draw.rectangle([cx - 18, cy - 10, cx - 4, cy + 4], fill=color)
    draw.rectangle([cx + 4, cy - 10, cx + 18, cy + 4], fill=color)
    draw.rectangle([cx - 18, cy + 4, cx + 18, cy + 12], fill=color)
    draw.rectangle([cx - 12, cy + 12, cx + 12, cy + 18], fill=color)
    draw.rectangle([cx - 6, cy + 18, cx + 6, cy + 24], fill=color)
    draw.rectangle([cx - 10, cy - 6, cx - 4, cy], fill=_WHITE)


def _draw_pickaxe(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 4, cy - 6, cx + 4, cy + 30], fill=_LEATHER)
    draw.rectangle([cx - 28, cy - 16, cx + 28, cy - 4], fill=_IRON, outline=(60, 60, 60))
    draw.rectangle([cx - 34, cy - 12, cx - 24, cy - 2], fill=_IRON)
    draw.rectangle([cx + 24, cy - 12, cx + 34, cy - 2], fill=_IRON)


def _draw_fish(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 26, cy - 8, cx + 16, cy + 12], fill=_WATER, outline=(20, 40, 100))
    draw.rectangle([cx + 16, cy - 16, cx + 28, cy - 4], fill=_WATER)
    draw.rectangle([cx + 16, cy + 8, cx + 28, cy + 20], fill=_WATER)
    draw.rectangle([cx - 16, cy - 4, cx - 10, cy + 2], fill=_WHITE)
    draw.rectangle([cx - 14, cy - 3, cx - 11, cy + 1], fill=(20, 20, 20))


def _draw_emerald(draw, cx: int, cy: int) -> None:
    draw.polygon(
        [(cx, cy - 28), (cx + 24, cy - 10), (cx + 18, cy + 22), (cx, cy + 30),
         (cx - 18, cy + 22), (cx - 24, cy - 10)],
        fill=(46, 204, 113),
        outline=(20, 100, 60),
    )
    draw.rectangle([cx - 8, cy - 12, cx + 2, cy - 2], fill=(150, 255, 200))


def _draw_wheat(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 4, cy - 10, cx + 4, cy + 32], fill=(110, 160, 50))
    for offset in (-18, -6, 6, 18):
        draw.rectangle([cx + offset - 4, cy - 24, cx + offset + 4, cy - 6], fill=_GOLD)
        draw.rectangle([cx + offset - 6, cy - 22, cx + offset - 2, cy - 12], fill=(255, 230, 120))


def _draw_house(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 28, cy - 4, cx + 28, cy + 30], fill=_WOOD, outline=(80, 50, 25))
    draw.polygon([(cx - 34, cy - 4), (cx, cy - 32), (cx + 34, cy - 4)], fill=_RED,
                 outline=(90, 30, 30))
    draw.rectangle([cx - 8, cy + 10, cx + 8, cy + 30], fill=(90, 60, 35))
    draw.rectangle([cx - 22, cy + 4, cx - 12, cy + 14], fill=(120, 200, 255))


def _draw_tnt(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 30, cy - 22, cx + 30, cy + 24], fill=_RED, outline=(80, 20, 20))
    draw.rectangle([cx - 30, cy - 6, cx + 30, cy + 8], fill=_WHITE)
    draw.rectangle([cx - 4, cy - 32, cx + 4, cy - 22], fill=(120, 80, 40))
    draw.rectangle([cx + 4, cy - 36, cx + 16, cy - 28], fill=(255, 190, 40))
    draw.rectangle([cx - 22, cy - 16, cx - 8, cy - 10], fill=(255, 120, 120))
    draw.rectangle([cx + 8, cy + 12, cx + 22, cy + 18], fill=(255, 120, 120))


def _draw_book(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 26, cy - 28, cx + 26, cy + 28], fill=(120, 70, 190),
                   outline=(60, 30, 110))
    draw.rectangle([cx - 18, cy - 20, cx + 18, cy + 20], fill=(230, 220, 255))
    draw.rectangle([cx - 4, cy - 20, cx + 4, cy + 20], fill=(120, 70, 190))
    draw.rectangle([cx + 8, cy - 12, cx + 14, cy - 6], fill=_GOLD)


def _draw_furnace(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 28, cy - 24, cx + 28, cy + 28], fill=_STONE, outline=(70, 70, 70))
    draw.rectangle([cx - 16, cy - 4, cx + 16, cy + 18], fill=(40, 30, 25))
    draw.rectangle([cx - 10, cy + 4, cx + 10, cy + 14], fill=(255, 140, 30))
    draw.rectangle([cx - 6, cy - 2, cx + 6, cy + 8], fill=(255, 220, 80))


def _draw_crafting_table(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 30, cy - 16, cx + 30, cy + 28], fill=_WOOD, outline=(80, 50, 25))
    for row in range(2):
        for col in range(2):
            x = cx - 20 + col * 22
            y = cy - 8 + row * 20
            draw.rectangle([x, y, x + 16, y + 14], fill=(190, 140, 85),
                           outline=(90, 55, 30))


def _draw_bread(draw, cx: int, cy: int) -> None:
    draw.rectangle([cx - 28, cy - 12, cx + 28, cy + 14], fill=(190, 130, 70),
                   outline=(100, 60, 30))
    draw.rectangle([cx - 18, cy - 6, cx - 8, cy], fill=(230, 180, 110))
    draw.rectangle([cx - 2, cy - 6, cx + 8, cy], fill=(230, 180, 110))
    draw.rectangle([cx + 14, cy - 6, cx + 22, cy], fill=(230, 180, 110))


def _draw_star(draw, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    draw.rectangle([cx - 4, cy - 28, cx + 4, cy + 28], fill=color)
    draw.rectangle([cx - 28, cy - 4, cx + 28, cy + 4], fill=color)
    draw.rectangle([cx - 18, cy - 18, cx + 18, cy + 18], fill=color)
    draw.rectangle([cx - 10, cy - 10, cx + 10, cy + 10], fill=_WHITE)


def _draw_icon(draw, action: str, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    if action == "mine":
        _draw_pickaxe(draw, cx, cy)
    elif action == "craft":
        _draw_crafting_table(draw, cx, cy)
    elif action == "smelt":
        _draw_furnace(draw, cx, cy)
    elif action == "enchant":
        _draw_book(draw, cx, cy)
    elif action == "fish":
        _draw_fish(draw, cx, cy)
    elif action == "farm":
        _draw_wheat(draw, cx, cy)
    elif action in {"trade", "tame"}:
        _draw_emerald(draw, cx, cy)
    elif action == "feed":
        _draw_bread(draw, cx, cy)
    elif action == "build":
        _draw_house(draw, cx, cy)
    elif action in {"bonk", "slap", "yeet", "roast"}:
        _draw_tnt(draw, cx, cy)
    elif action in {"stare", "shrug", "facepalm", "laugh", "cry", "salute"}:
        _draw_star(draw, cx, cy, color)
    else:
        _draw_heart(draw, cx, cy, color)


def _render_card(action: str, title: str, color: int, category: str) -> bytes:
    from PIL import Image, ImageDraw

    accent = _rgb(color)
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (135, 206, 235))
    draw = ImageDraw.Draw(image)

    # Soft blocky sky gradient.
    for y in range(0, 112, 4):
        ratio = y / 112
        sky = (
            int(135 + (210 - 135) * ratio),
            int(206 + (235 - 206) * ratio),
            int(235 + (255 - 235) * ratio),
        )
        draw.rectangle([0, y, CARD_WIDTH, y + 4], fill=sky)

    # Clouds.
    for x, y in ((28, 22), (206, 16), (360, 28)):
        draw.rectangle([x, y, x + 58, y + 14], fill=(250, 250, 255))
        draw.rectangle([x + 12, y - 8, x + 46, y + 6], fill=(250, 250, 255))

    # Grass blocks.
    for index, x in enumerate(range(0, CARD_WIDTH, 32)):
        top = _LEAF if index % 2 == 0 else (46, 130, 50)
        draw.rectangle([x, 112, x + 32, CARD_HEIGHT], fill=(120, 85, 55))
        draw.rectangle([x, 112, x + 32, 124], fill=top, outline=(30, 90, 35))

    # Characters and a shared action icon.
    _draw_character(draw, 62, 28, accent)
    _draw_character(draw, 344, 28, (90, 150, 220))
    _draw_icon(draw, action, 240, 64, accent)

    # Title plate.
    draw.rectangle([12, 8, 224, 34], fill=(30, 30, 30))
    draw.text((20, 12), f"JUNIOR ATLAS  •  {title.upper()}", fill=_WHITE, font=_font(15))

    # Category tag.
    tag = category.upper()
    draw.rectangle([CARD_WIDTH - 118, 8, CARD_WIDTH - 12, 32], fill=(30, 30, 30))
    draw.text((CARD_WIDTH - 110, 12), tag, fill=accent, font=_font(14))

    draw.rectangle([0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1], outline=accent, width=4)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@lru_cache(maxsize=64)
def render_action_card(
    action: str,
    title: str,
    color: int,
    category: str = "Minecraft",
) -> bytes | None:
    """Return PNG bytes for an interaction card, or ``None`` on failure."""
    try:
        return _render_card(action, title, color, category)
    except Exception:
        log.debug("pixel-art card rendering failed action=%s", action, exc_info=True)
        return None

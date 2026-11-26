"""Original Minecraft-themed interaction catalogue for Junior Atlas.

The catalogue is intentionally data-driven: command registration, embeds,
response variation, help metadata and Friendship XP all read from the same
specs.  Nothing here depends on an external GIF provider.
"""
from __future__ import annotations

from dataclasses import dataclass

HELP_CATEGORY = "Minecraft"
FUN_CATEGORY = "Fun"
XP_COOLDOWN_SECONDS = 30

# Minecraft-inspired palette used by the interaction embeds.
GRASS = 0x5EBB2B
DIAMOND = 0x4AEDD9
REDSTONE = 0xE03C3C
GOLD = 0xF2C94C
LAPIS = 0x2F5FDE
EMERALD = 0x2ECC71
AMETHYST = 0x9B59B6
OAK = 0xB07A4A
ROSE = 0xE86A92
NETHER = 0x8B2E2E
SKY = 0x87CEEB


@dataclass(frozen=True)
class ActionSpec:
    """A single interaction command and its presentation data."""

    name: str
    title: str
    category: str
    emoji: str
    description: str
    color: int
    xp: int
    gif_key: str
    uses_gif: bool
    initial_verb: str
    reciprocate_verb: str
    button_label: str
    responses: tuple[str, ...]
    reciprocal_responses: tuple[str, ...]
    self_responses: tuple[str, ...]
    example_prefix: str
    example_slash: str


def _spec(
    name: str,
    title: str,
    category: str,
    emoji: str,
    description: str,
    color: int,
    xp: int,
    *,
    gif_key: str | None = None,
    uses_gif: bool = True,
    initial_verb: str,
    reciprocate_verb: str,
    button_label: str,
    responses: tuple[str, ...],
    reciprocal_responses: tuple[str, ...],
    self_responses: tuple[str, ...],
) -> ActionSpec:
    return ActionSpec(
        name=name,
        title=title,
        category=category,
        emoji=emoji,
        description=description,
        color=color,
        xp=xp,
        gif_key=gif_key or name,
        uses_gif=uses_gif,
        initial_verb=initial_verb,
        reciprocate_verb=reciprocate_verb,
        button_label=button_label,
        responses=responses,
        reciprocal_responses=reciprocal_responses,
        self_responses=self_responses,
        example_prefix=f",{name} @member",
        example_slash=f"/{name} member:@member",
    )


_ACTIONS: tuple[ActionSpec, ...] = (
    # ------------------------------------------------------------------ social
    _spec(
        "hug", "Hug", "Social", "🤗",
        "Share a warm hug with someone", ROSE, 10,
        initial_verb="gave a warm hug to",
        reciprocate_verb="hugged back",
        button_label="Hug back!",
        responses=(
            "{actor} wrapped {target} in a cozy wool-blanket hug.",
            "{actor} gave {target} a warm hug. The nearby wolves approved.",
            "{actor} hugged {target} like a teddy bear at spawn.",
            "{actor} shared a marshmallow-soft hug with {target}.",
        ),
        reciprocal_responses=(
            "{target} hugged {actor} back! A perfect friendship combo.",
            "{target} returned the hug with extra wool-fluff.",
            "{target} squeezed {actor} in a warm return hug.",
        ),
        self_responses=(
            "{actor} hugged a plush creeper. It was surprisingly soft.",
            "{actor} wrapped themselves in a wool blanket and called it a hug.",
            "{actor} gave the nearest crafting table a very sincere hug.",
        ),
    ),
    _spec(
        "pat", "Pat", "Social", "🫳",
        "Give someone a friendly pat", GOLD, 10,
        initial_verb="gave a friendly pat to",
        reciprocate_verb="patted back",
        button_label="Pat back!",
        responses=(
            "{actor} gave {target} a gentle pat. +1 block of kindness.",
            "{actor} patted {target} on the head like a happy wolf.",
            "{actor} used a soft pat on {target}. It was super effective!",
        ),
        reciprocal_responses=(
            "{target} patted {actor} back. The helmet is fine.",
            "{target} returned the pat with a tiny 'boop' sound.",
        ),
        self_responses=(
            "{actor} patted their own helmet. It echoed nicely.",
            "{actor} gave a passing wolf a very gentle pat.",
        ),
    ),
    _spec(
        "poke", "Poke", "Social", "👉",
        "Poke someone to get their attention", LAPIS, 10,
        initial_verb="poked",
        reciprocate_verb="poked back",
        button_label="Poke back!",
        responses=(
            "{actor} poked {target}. A redstone signal fired somewhere.",
            "{actor} poked {target} and a piston extended.",
            "{actor} gave {target} a curious poke. No blocks were harmed.",
        ),
        reciprocal_responses=(
            "{target} poked {actor} back. The circuit is complete.",
            "{target} poked {actor} and a hidden door opened.",
        ),
        self_responses=(
            "{actor} poked a button. The iron door opened.",
            "{actor} poked a slime. It wobbled thoughtfully.",
        ),
    ),
    _spec(
        "cuddle", "Cuddle", "Social", "🫂",
        "Cuddle up with someone", ROSE, 10,
        initial_verb="cuddled",
        reciprocate_verb="cuddled back",
        button_label="Cuddle back!",
        responses=(
            "{actor} cuddled up next to {target} by the campfire.",
            "{actor} shared a warm cuddle with {target} while the furnace crackled.",
            "{actor} cuddled {target} like two cats on a chest.",
        ),
        reciprocal_responses=(
            "{target} cuddled {actor} back. Maximum coziness achieved.",
            "{target} wrapped {actor} in a blanket burrito.",
        ),
        self_responses=(
            "{actor} cuddled a pile of soft wool blocks.",
            "{actor} made a blanket fort and cuddled a pillow.",
        ),
    ),
    _spec(
        "wave", "Wave", "Social", "👋",
        "Wave hello to someone", SKY, 10,
        initial_verb="waved at",
        reciprocate_verb="waved back at",
        button_label="Wave back!",
        responses=(
            "{actor} waved at {target} from across the village.",
            "{actor} waved to {target}. A nearby villager waved too.",
            "{actor} gave {target} a friendly wave from the top of a hill.",
        ),
        reciprocal_responses=(
            "{target} waved back at {actor}. Friendship signal received.",
            "{target} waved so hard their arm made a whoosh sound.",
        ),
        self_responses=(
            "{actor} waved at a passing cloud.",
            "{actor} waved at a wandering trader. The llamas nodded.",
        ),
    ),
    _spec(
        "highfive", "High Five", "Social", "✋",
        "Give someone a high-five", GOLD, 10,
        gif_key="highfive",
        initial_verb="gave a high-five to",
        reciprocate_verb="high-fived back",
        button_label="High-five back!",
        responses=(
            "{actor} and {target} shared a perfectly timed high-five.",
            "{actor} high-fived {target}. The sound echoed through the cave.",
            "{actor} high-fived {target} so hard a bat flew out of the cave.",
        ),
        reciprocal_responses=(
            "{target} high-fived {actor} back. Perfect sync!",
            "{target} added a celebratory sparkle to the high-five.",
        ),
        self_responses=(
            "{actor} high-fived a mirror. It was a solid hit.",
            "{actor} high-fived a tree. The leaves applauded.",
        ),
    ),
    _spec(
        "boop", "Boop", "Social", "👉",
        "Boop someone on the nose", AMETHYST, 10,
        gif_key="boop",
        initial_verb="booped",
        reciprocate_verb="booped back",
        button_label="Boop back!",
        responses=(
            "{actor} booped {target} on the nose. A tiny 'boop' echoed.",
            "{actor} booped {target} with a feather. Critical cuteness!",
            "{actor} booped {target}. The slime bounced happily.",
        ),
        reciprocal_responses=(
            "{target} booped {actor} back. Boop chain initiated.",
            "{target} delivered a perfectly timed return boop.",
        ),
        self_responses=(
            "{actor} booped a slime. It split into two happy slimes.",
            "{actor} booped a button and a lamp turned on.",
        ),
    ),
    _spec(
        "comfort", "Comfort", "Social", "🍲",
        "Comfort someone with kind words", EMERALD, 10,
        gif_key="comfort",
        initial_verb="comforted",
        reciprocate_verb="comforted back",
        button_label="Comfort back!",
        responses=(
            "{actor} sat beside {target} and offered a warm bowl of mushroom stew.",
            "{actor} comforted {target} with a soft blanket and a torch.",
            "{actor} reminded {target} that even the best builds need a break.",
        ),
        reciprocal_responses=(
            "{target} comforted {actor} back with a golden carrot.",
            "{target} shared a cozy campfire story with {actor}.",
        ),
        self_responses=(
            "{actor} made themselves a cozy campfire and took a deep breath.",
            "{actor} drank a warm potion and felt a little better.",
        ),
    ),
    _spec(
        "cheer", "Cheer", "Social", "🎉",
        "Cheer someone on", GOLD, 10,
        gif_key="cheer",
        initial_verb="cheered for",
        reciprocate_verb="cheered back for",
        button_label="Cheer back!",
        responses=(
            "{actor} cheered for {target}! The whole village clapped.",
            "{actor} cheered {target} on with a chorus of parrots.",
            "{actor} threw confetti made of paper and redstone dust for {target}.",
        ),
        reciprocal_responses=(
            "{target} cheered for {actor} too. Double the hype!",
            "{target} started a victory dance for {actor}.",
        ),
        self_responses=(
            "{actor} cheered for their own next big build.",
            "{actor} rang a bell and cheered at the sky.",
        ),
    ),
    _spec(
        "dance", "Dance", "Social", "💃",
        "Dance with someone", AMETHYST, 10,
        initial_verb="started dancing with",
        reciprocate_verb="danced along with",
        button_label="Dance back!",
        responses=(
            "{actor} danced with {target} around the campfire.",
            "{actor} and {target} busted moves to the jukebox.",
            "{actor} pulled {target} into a blocky dance party.",
        ),
        reciprocal_responses=(
            "{target} joined {actor} for an encore dance.",
            "{target} showed {actor} the legendary creeper shuffle.",
        ),
        self_responses=(
            "{actor} danced with a jukebox until the disc ended.",
            "{actor} practiced the villager head-bob in the mirror.",
        ),
    ),
    # --------------------------------------------------------------- minecraft
    _spec(
        "mine", "Mine", "Minecraft", "⛏️",
        "Go mining with someone", DIAMOND, 12,
        uses_gif=False,
        initial_verb="went mining with",
        reciprocate_verb="mined alongside",
        button_label="Mine together!",
        responses=(
            "{actor} and {target} went mining together and discovered diamonds!",
            "{actor} and {target} dug a tunnel and found a vein of iron.",
            "{actor} handed {target} a pickaxe and they struck lapis.",
            "{actor} and {target} followed a cave until they found amethyst.",
        ),
        reciprocal_responses=(
            "{target} took {actor} mining and found even more diamonds!",
            "{target} handed {actor} a spare pickaxe for the next expedition.",
        ),
        self_responses=(
            "{actor} went mining and found a shiny diamond. Lucky day!",
            "{actor} dug straight down. Fortunately, there was a ladder.",
        ),
    ),
    _spec(
        "craft", "Craft", "Minecraft", "🛠️",
        "Craft something with someone", OAK, 12,
        uses_gif=False,
        initial_verb="crafted with",
        reciprocate_verb="crafted alongside",
        button_label="Craft together!",
        responses=(
            "{actor} crafted a friendship with {target} at the crafting table!",
            "{actor} and {target} crafted a matching pair of oak boats.",
            "{actor} showed {target} a secret recipe: one heart, two sticks.",
            "{actor} and {target} filled a chest with freshly crafted tools.",
        ),
        reciprocal_responses=(
            "{target} crafted a friendship bracelet for {actor}.",
            "{target} saved {actor} a spot at the crafting table.",
        ),
        self_responses=(
            "{actor} crafted a tiny wooden chair and felt productive.",
            "{actor} crafted a stack of sticks. No plan yet, but hopeful.",
        ),
    ),
    _spec(
        "smelt", "Smelt", "Minecraft", "🔥",
        "Smelt ore with someone", REDSTONE, 12,
        uses_gif=False,
        initial_verb="smelted ore with",
        reciprocate_verb="smelted alongside",
        button_label="Smelt together!",
        responses=(
            "{actor} and {target} smelted a batch of iron. The furnace is toasty!",
            "{actor} smelted ore with {target} and shared the last coal.",
            "{actor} and {target} watched the furnace bubble. Perfect teamwork.",
        ),
        reciprocal_responses=(
            "{target} smelted a golden ingot for {actor}.",
            "{target} kept the furnace warm for {actor}'s next batch.",
        ),
        self_responses=(
            "{actor} smelted a stack of cobblestone just to watch the flames.",
            "{actor} smelted a potato. It was technically progress.",
        ),
    ),
    _spec(
        "enchant", "Enchant", "Minecraft", "✨",
        "Enchant someone with friendship", AMETHYST, 12,
        uses_gif=False,
        initial_verb="enchanted",
        reciprocate_verb="enchanted back",
        button_label="Enchant back!",
        responses=(
            "{actor} enchanted {target} with Friendship III!",
            "{actor} enchanted {target}'s boots with Feather Falling IV.",
            "{actor} spent 30 levels enchanting {target} with good vibes.",
        ),
        reciprocal_responses=(
            "{target} enchanted {actor} with Loyalty III.",
            "{target} added Unbreaking III to {actor}'s friendship armor.",
        ),
        self_responses=(
            "{actor} enchanted their own pickaxe with Efficiency V.",
            "{actor} enchanted a book and hid it in a chest.",
        ),
    ),
    _spec(
        "fish", "Fish", "Minecraft", "🎣",
        "Go fishing with someone", LAPIS, 12,
        uses_gif=False,
        initial_verb="went fishing with",
        reciprocate_verb="fished alongside",
        button_label="Fish together!",
        responses=(
            "{actor} and {target} went fishing and caught a legendary tropical fish!",
            "{actor} and {target} fished by the river and caught a boot. A fancy boot.",
            "{actor} taught {target} the ancient art of waiting for bubbles.",
        ),
        reciprocal_responses=(
            "{target} reeled in a treasure map for {actor}.",
            "{target} saved {actor} the biggest fish of the day.",
        ),
        self_responses=(
            "{actor} went fishing and caught a very surprised cod.",
            "{actor} fished up a name tag. Now to find a worthy pet.",
        ),
    ),
    _spec(
        "farm", "Farm", "Minecraft", "🌾",
        "Farm crops with someone", GRASS, 12,
        uses_gif=False,
        initial_verb="farmed with",
        reciprocate_verb="farmed alongside",
        button_label="Farm together!",
        responses=(
            "{actor} and {target} harvested a golden wheat field together.",
            "{actor} and {target} planted carrots until the sun went down.",
            "{actor} showed {target} how to make bonemeal from skeletons.",
        ),
        reciprocal_responses=(
            "{target} harvested a pumpkin for {actor}.",
            "{target} saved {actor} a seat on the hay bales.",
        ),
        self_responses=(
            "{actor} farmed a neat row of wheat and felt like a pro.",
            "{actor} traded a villager for a very promising beetroot seed.",
        ),
    ),
    _spec(
        "trade", "Trade", "Minecraft", "💎",
        "Trade with someone", EMERALD, 12,
        uses_gif=False,
        initial_verb="traded with",
        reciprocate_verb="traded back with",
        button_label="Trade back!",
        responses=(
            "{actor} traded emeralds with {target} for a very fair deal!",
            "{actor} and {target} swapped blocks like seasoned villagers.",
            "{actor} traded {target} a stack of wheat for a shiny emerald.",
        ),
        reciprocal_responses=(
            "{target} gave {actor} a discount. Villager approved!",
            "{target} traded {actor} a rare map for a friendly handshake.",
        ),
        self_responses=(
            "{actor} tried to trade with a wandering trader. It went poorly.",
            "{actor} traded a villager 32 sticks for one emerald. Bargain!",
        ),
    ),
    _spec(
        "tame", "Tame", "Minecraft", "🐺",
        "Tame someone with a golden apple", GOLD, 12,
        uses_gif=False,
        initial_verb="tamed",
        reciprocate_verb="tamed back",
        button_label="Tame back!",
        responses=(
            "{actor} successfully tamed {target} using a golden apple!",
            "{actor} tamed {target} with a bone and a lot of patience.",
            "{actor} earned {target}'s trust. A new wolf friend joined the party.",
        ),
        reciprocal_responses=(
            "{target} tamed {actor} with a golden carrot. Loyalty unlocked!",
            "{target} offered {actor} a bone and a permanent party invite.",
        ),
        self_responses=(
            "{actor} tamed a wolf with a bone. It immediately sat on the bed.",
            "{actor} tamed a cat with raw salmon. The cat owns the base now.",
        ),
    ),
    _spec(
        "feed", "Feed", "Minecraft", "🍞",
        "Feed someone a snack", OAK, 12,
        uses_gif=False,
        initial_verb="fed a snack to",
        reciprocate_verb="fed a snack back to",
        button_label="Feed back!",
        responses=(
            "{actor} fed {target} a freshly baked bread. Nom nom!",
            "{actor} shared a golden apple with {target}. Health restored!",
            "{actor} fed {target} a bowl of mushroom stew by the fire.",
        ),
        reciprocal_responses=(
            "{target} fed {actor} a cookie. Sweet revenge!",
            "{target} handed {actor} a baked potato with extra butter.",
        ),
        self_responses=(
            "{actor} ate a golden apple and felt invincible.",
            "{actor} made a suspicious stew. The effects were interesting.",
        ),
    ),
    _spec(
        "build", "Build", "Minecraft", "🏠",
        "Build something with someone", OAK, 12,
        uses_gif=False,
        initial_verb="built with",
        reciprocate_verb="built alongside",
        button_label="Build together!",
        responses=(
            "{actor} and {target} built a cozy oak cabin before nightfall!",
            "{actor} and {target} placed the last block of a brand-new tower.",
            "{actor} helped {target} build a bridge over a very inconvenient ravine.",
        ),
        reciprocal_responses=(
            "{target} added a balcony to {actor}'s build. Fancy!",
            "{target} placed a lantern so {actor}'s build would look cozy.",
        ),
        self_responses=(
            "{actor} built a tiny house for a stray cat.",
            "{actor} built a dirt hut and called it 'rustic'.",
        ),
    ),
    # ---------------------------------------------------------------- playful
    _spec(
        "bonk", "Bonk", "Playful", "🔨",
        "Give someone a playful bonk", REDSTONE, 8,
        gif_key="bonk",
        initial_verb="bonked",
        reciprocate_verb="bonked back",
        button_label="Bonk back!",
        responses=(
            "{actor} bonked {target} with a foam pickaxe. No durability lost!",
            "{actor} gave {target} a gentle bonk. The anvil rang softly.",
            "{actor} bonked {target} into a pile of leaves.",
        ),
        reciprocal_responses=(
            "{target} bonked {actor} back. Bonk protocol complete.",
            "{target} returned the bonk with a very soft hammer.",
        ),
        self_responses=(
            "{actor} bonked a training dummy. It took 1 damage.",
            "{actor} bonked a tree. The tree bonked back with an apple.",
        ),
    ),
    _spec(
        "slap", "Slap", "Playful", "🖐️",
        "Slap someone with a fish", NETHER, 8,
        gif_key="slap",
        initial_verb="playfully slapped",
        reciprocate_verb="playfully slapped back",
        button_label="Slap back!",
        responses=(
            "{actor} slapped {target} with a raw cod. Splash!",
            "{actor} delivered a dramatic slap with a wet sponge.",
            "{actor} slapped {target} with a book. Page 42, specifically.",
        ),
        reciprocal_responses=(
            "{target} slapped {actor} back with a feather. Duel accepted.",
            "{target} returned fire with a very soggy cod.",
        ),
        self_responses=(
            "{actor} slapped a mosquito. The swamp is safer now.",
            "{actor} slapped a slime and immediately apologized.",
        ),
    ),
    _spec(
        "yeet", "Yeet", "Playful", "🚀",
        "Yeet someone into the End", REDSTONE, 8,
        gif_key="yeet",
        initial_verb="yeeted",
        reciprocate_verb="yeeted back",
        button_label="Yeet back!",
        responses=(
            "{actor} yeeted {target} into the End portal!",
            "{actor} launched {target} over a ravine with a well-placed piston.",
            "{actor} yeeted {target} into the village fountain.",
        ),
        reciprocal_responses=(
            "{target} yeeted {actor} right back. Round two!",
            "{target} caught {actor} with a perfectly placed slime block.",
        ),
        self_responses=(
            "{actor} yeeted a snowball into the sunset.",
            "{actor} yeeted a piece of cobblestone into a very deep hole.",
        ),
    ),
    _spec(
        "roast", "Roast", "Playful", "🔥",
        "Roast someone in a blast furnace", REDSTONE, 8,
        gif_key="roast",
        initial_verb="roasted",
        reciprocate_verb="roasted back",
        button_label="Roast back!",
        responses=(
            "{actor} roasted {target} in a blast furnace. Extra crispy!",
            "{actor} roasted {target}'s build with a perfectly timed one-liner.",
            "{actor} turned up the heat on {target}. The campfire is jealous.",
        ),
        reciprocal_responses=(
            "{target} roasted {actor} back. The furnace is at max heat!",
            "{target} served {actor} a perfectly toasted comeback.",
        ),
        self_responses=(
            "{actor} roasted a potato. It was deliciously savage.",
            "{actor} roasted a marshmallow and burned it. Classic.",
        ),
    ),
    _spec(
        "stare", "Stare", "Playful", "👀",
        "Stare at someone like an Enderman", AMETHYST, 8,
        gif_key="stare",
        initial_verb="stared at",
        reciprocate_verb="stared back at",
        button_label="Stare back!",
        responses=(
            "{actor} stared at {target} like an Enderman.",
            "{actor} and {target} had a staring contest. The parrots bet on it.",
            "{actor} stared at {target} until a creeper politely coughed.",
        ),
        reciprocal_responses=(
            "{target} stared back at {actor}. Nobody blinked.",
            "{target} matched {actor}'s stare and raised an eyebrow.",
        ),
        self_responses=(
            "{actor} stared at a painting for three minutes.",
            "{actor} stared at an Enderman. That was a mistake.",
        ),
    ),
    _spec(
        "shrug", "Shrug", "Playful", "🤷",
        "Shrug at someone", SKY, 8,
        gif_key="shrug",
        initial_verb="shrugged at",
        reciprocate_verb="shrugged back at",
        button_label="Shrug back!",
        responses=(
            "{actor} shrugged at {target}. The villagers are confused.",
            "{actor} gave {target} a shrug that said 'redstone is hard'.",
            "{actor} shrugged at {target} and placed a question-mark sign.",
        ),
        reciprocal_responses=(
            "{target} shrugged back at {actor}. Mystery remains.",
            "{target} shrugged so hard their shoulders made a creak.",
        ),
        self_responses=(
            "{actor} shrugged at a broken redstone circuit.",
            "{actor} shrugged at the concept of Monday.",
        ),
    ),
    _spec(
        "facepalm", "Facepalm", "Playful", "🤦",
        "Facepalm at someone", OAK, 8,
        gif_key="facepalm",
        initial_verb="facepalmed at",
        reciprocate_verb="facepalmed back at",
        button_label="Facepalm back!",
        responses=(
            "{actor} facepalmed at {target}'s redstone contraption.",
            "{actor} facepalmed as {target}'s piston launched the wrong block.",
            "{actor} gave {target} the loudest silent facepalm.",
        ),
        reciprocal_responses=(
            "{target} facepalmed back at {actor}. The contraption is still broken.",
            "{target} sighed and facepalmed at the same time.",
        ),
        self_responses=(
            "{actor} facepalmed at their own lava placement.",
            "{actor} facepalmed after mining straight into a ravine.",
        ),
    ),
    _spec(
        "laugh", "Laugh", "Playful", "😂",
        "Laugh with someone", GOLD, 8,
        gif_key="laugh",
        initial_verb="laughed with",
        reciprocate_verb="laughed back with",
        button_label="Laugh back!",
        responses=(
            "{actor} laughed with {target} until the parrots joined in.",
            "{actor} and {target} laughed at a very serious chicken.",
            "{actor} laughed so hard {target} dropped their pickaxe.",
        ),
        reciprocal_responses=(
            "{target} laughed back with {actor}. Comedy achieved!",
            "{target} added a snort to {actor}'s joke.",
        ),
        self_responses=(
            "{actor} laughed at a pig wearing a saddle.",
            "{actor} laughed at their own joke. It was a good one.",
        ),
    ),
    _spec(
        "cry", "Cry", "Playful", "😢",
        "Cry with someone", LAPIS, 8,
        gif_key="cry",
        initial_verb="cried with",
        reciprocate_verb="cried with",
        button_label="Cry back!",
        responses=(
            "{actor} cried with {target} in the rain. The wolves howled along.",
            "{actor} and {target} cried happy tears over a beautiful sunset.",
            "{actor} cried when {target}'s dog sat on the bed. So sweet.",
        ),
        reciprocal_responses=(
            "{target} cried with {actor}. Emotional support acquired.",
            "{target} offered {actor} a tissue and a warm blanket.",
        ),
        self_responses=(
            "{actor} cried over a broken diamond pickaxe.",
            "{actor} cried at a very touching painting.",
        ),
    ),
    _spec(
        "salute", "Salute", "Playful", "🎖️",
        "Salute someone", EMERALD, 8,
        gif_key="salute",
        initial_verb="saluted",
        reciprocate_verb="saluted back",
        button_label="Salute back!",
        responses=(
            "{actor} saluted {target}. A true block-building hero!",
            "{actor} gave {target} a crisp salute from atop the fortress.",
            "{actor} saluted {target} for surviving the Nether.",
        ),
        reciprocal_responses=(
            "{target} saluted {actor} back. Honor restored.",
            "{target} returned the salute with a ceremonial pickaxe raise.",
        ),
        self_responses=(
            "{actor} saluted the sunrise over their base.",
            "{actor} saluted a very brave chicken crossing the road.",
        ),
    ),
)

MINECRAFT_ACTIONS: dict[str, ActionSpec] = {spec.name: spec for spec in _ACTIONS}
ACTION_ORDER: tuple[str, ...] = tuple(spec.name for spec in _ACTIONS)

SOCIAL_ACTIONS = tuple(spec.name for spec in _ACTIONS if spec.category == "Social")
MINECRAFT_ONLY_ACTIONS = tuple(
    spec.name for spec in _ACTIONS if spec.category == "Minecraft"
)
PLAYFUL_ACTIONS = tuple(spec.name for spec in _ACTIONS if spec.category == "Playful")


def get_action(name: str) -> ActionSpec | None:
    return MINECRAFT_ACTIONS.get(name)


def action_emoji(name: str) -> str:
    spec = MINECRAFT_ACTIONS.get(name)
    return spec.emoji if spec else "✨"


def action_extras(spec: ActionSpec) -> dict:
    """Help metadata shared by prefix and slash command registrations."""
    return {
        "help_category": (
            HELP_CATEGORY if spec.category == HELP_CATEGORY else FUN_CATEGORY
        ),
        "action": spec.name,
        "action_category": spec.category,
        "usage_prefix": f"<prefix>{spec.name} [member]",
        "usage_slash": f"/{spec.name} [member]",
        "example_prefix": spec.example_prefix,
        "example_slash": spec.example_slash,
        "cooldown": f"{XP_COOLDOWN_SECONDS}s Friendship XP cooldown",
        "permissions": "Send Messages; Embed Links (bot)",
    }

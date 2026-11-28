# Minecraft RPG — OwO-style Parity Audit & Implementation Plan

> **Status:** living plan. Phase 1 is implemented in this repository; later phases are
> tracked here so the work never silently stops at a small command subset.
>
> **Legal boundary:** this project reimplements *game mechanics* with original code,
> Minecraft terminology and emoji/text presentation. It does not copy OwO Bot source,
> private APIs, artwork, response text, or branding.

## 1. Repository audit (actual baseline)

| Item | Finding |
|---|---|
| Language / runtime | Python 3.12+, async |
| Discord library | `discord.py` 2.7.1 (`commands.AutoShardedBot`) |
| Database | PostgreSQL 17 via SQLAlchemy 2 async + asyncpg |
| Migrations | Alembic, linear head `0030_minecraft_interactions` before this work |
| Cache / coordination | Redis 8 (`RedisCache`, distributed rate limiter, shard leases) |
| Background work | ARQ workers, scheduler, gateway worker pool, greeting worker |
| Command surface | Slash tree + per-guild prefix commands; **global-only sync** |
| Root slash-command budget | Discord hard limit 100; current tree is already large |
| Existing economy | `Economy` model, `EconomyTransaction` ledger, `ShopItem`, `UserInventory`, `EconomyService`, `EconomyRepository` |
| Existing games | Tic-tac-toe, RPS, trivia, UNO, hand cricket, game sessions/stats |
| Existing social | Minecraft interaction catalogue (hug/pat/etc.), Friendship XP |
| Existing leveling | Levels, XP, roles, leaderboards, achievements |
| Existing community | Profiles, reputation, collectibles, polls, giveaways, temp voice |
| **Missing RPG core** | No hunt/battle/zoo/pets/weapons/crates/quests/bazaar |
| **Inconsistency found** | `PlatformService.change_balance` wrote `Economy.balance` only, while `EconomyRepository` treats `wallet` as authoritative. Fixed in Phase 1. |
| **Unwired service found** | `EconomyService` existed but was never attached to `Bot`. Wired in Phase 1. |

### Architecture constraints that shape the design

1. **Never create a second implementation of an existing feature.** Extend
   `EconomyService`, `EconomyRepository`, `ShopItem`, `UserInventory`.
2. **Never register duplicate commands.** `balance`, `daily`, `coinflip` already
   exist. New economy verbs go under an `economy` group / new names.
3. **Respect the 100-root-command limit.** New RPG and economy surfaces are
   `commands.GroupCog` groups (`/rpg`, `/economy`) plus flat prefix aliases, not
   dozens of new roots.
4. **Global sync only.** `command_sync` refuses duplicate scopes; do not add guild
   copies.
5. **No data resets.** New tables only. Existing `economy` rows keep their
   `balance`; `wallet` is the ledger-authoritative column.
6. **All mutating game actions are server-side validated.** No client-trusted
   results.
7. **Tests must not need a live database.** Services sit behind repositories that
   can be mocked, matching the existing `test_m7_economy.py` style.

## 2. Command parity table

Columns: **OwO reference** (publicly documented/observable behaviour) → **Minecraft
equivalent** → **repo status**. `NEW` means this plan adds it; `EXT` means an
existing feature is extended rather than duplicated.

### 2.1 Economy & progression

| OwO reference | Purpose | Minecraft equivalent | Status |
|---|---|---|---|
| `daily` | Daily reward + streak | `/daily` — "Daily Minecart Delivery" | EXT (exists) |
| `weekly` | Weekly reward | `/economy weekly` | Phase 1 |
| `work` | Timed job reward | `/economy work` — villager jobs | Phase 1 |
| `balance` | Wallet/bank view | `/balance` — emeralds | EXT (exists) |
| `bank deposit/withdraw` | Move money | `/economy deposit`, `/economy withdraw` | Phase 1 |
| `give` / `pay` | Transfer | `/economy pay` | Phase 1 |
| `coinflip` | 50/50 gamble | `/coinflip` | EXT (exists) |
| `slots` | Slot machine | `/economy slots` — "Redstone Reels" | Phase 1 |
| `rob` | Steal with risk | `/economy rob` | Phase 1 |
| `curse` | Bad-luck debuff | `/economy curse` | Phase 1 |
| `cookie` | Gift a cookie | `/economy cookie` | Phase 1 |
| `lottery` | Pooled draw | `/economy lottery` | Phase 2 |
| `quest` | Daily objectives | `/rpg quest`, `/rpg quest claim` | Phase 1 |
| `profile` | Stats card | `/rpg profile` | Phase 1 |
| `badges` | Achievement display | `/rpg badges` | Phase 2 |
| `title` / `bio` | Customisation | `/rpg title`, `/rpg bio` | Phase 2 |
| `rep` | Reputation | EXT `MemberProfile`/`Reputation` | Phase 3 |

### 2.2 Hunt / battle / collection loop

| OwO reference | Purpose | Minecraft equivalent | Status |
|---|---|---|---|
| `hunt` | Timed hunt, catch mobs, weapon drops | `/rpg hunt [biome]` | Phase 1 |
| `battle` | Fight a mob or player | `/rpg battle [member]` | Phase 1 |
| `zoo` | View captured mobs | `/rpg zoo` | Phase 1 |
| `sell` | Sell mobs/items | `/rpg sell <item>` | Phase 1 |
| `sacrifice` | Convert pets to currency | `/rpg sacrifice` | Phase 2 |
| `pets` | List pets | `/rpg pets` | Phase 1 |
| `pet` | Equip a pet | `/rpg pet <name>` | Phase 1 |
| `weapons` | List weapons | `/rpg weapons` | Phase 1 |
| `equip` | Equip weapon | `/rpg equip <weapon>` | Phase 1 |
| `inventory` / `inv` | Items | `/rpg inventory` | Phase 1 |
| `crate` | Buy + open crate | `/rpg crate <type>` | Phase 1 |
| `open` | Open owned crate | `/rpg open <type>` | Phase 1 |
| `lootbox` | Random box | Crate tiers | Phase 1 |
| `bazaar` | Player market | `/rpg bazaar` | Phase 3 |
| `shop` / `buy` | NPC shop | `/rpg shop`, `/rpg buy` | Phase 1 |
| `use` | Consume item | `/rpg use <item>` | Phase 2 |
| `trade` | Direct trade | `/rpg trade` | Phase 3 |
| `team` | Party | `/rpg team` | Phase 3 |
| `duel` | Staked PvP | `/rpg duel` | Phase 3 |

### 2.3 Social & relationship

| OwO reference | Purpose | Minecraft equivalent | Status |
|---|---|---|---|
| `hug/pat/kiss/slap/punch/...` | Interactions | Existing Minecraft catalogue | EXT (exists) |
| `marry` / `divorce` | Marriage | `/social marry`, `/social divorce` | Phase 3 |
| `adopt` / `disown` / `family` | Family tree | `/social family` | Phase 3 |
| `ship` | Compatibility | `/social ship` | Phase 3 |
| `cookie` | Gift | `/economy cookie` | Phase 1 |
| `profile` | Public card | `/rpg profile` | Phase 1 |

### 2.4 Games & fun

| OwO reference | Purpose | Minecraft equivalent | Status |
|---|---|---|---|
| `8ball` | Fortune | `/8ball` | EXT (exists) |
| `trivia` | Quiz | `/trivia` | EXT (exists) |
| `rps` | Rock paper scissors | `/rps` | EXT (exists) |
| `tictactoe` | Board game | `/tictactoe` | EXT (exists) |
| `uno` | Card game | `/uno` | EXT (exists) |
| `blackjack` / `21` | Card gamble | `/economy blackjack` | Phase 2 |
| `poker` | Card gamble | `/economy poker` | Phase 3 |
| `roulette` | Wheel gamble | `/economy roulette` | Phase 2 |
| `guess` | Number gamble | `/economy guess` | Phase 2 |
| `hangman` | Word game | `/hangman` | Phase 2 |
| `connect4` | Board game | `/connect4` | Phase 2 |
| `slots` | Reels | `/economy slots` | Phase 1 |

### 2.5 Utility & settings

| OwO reference | Purpose | Minecraft equivalent | Status |
|---|---|---|---|
| `help` | Searchable help | `/help` | EXT (exists) |
| `ping` | Latency | `/ping` | EXT (exists) |
| `avatar` / `userinfo` / `serverinfo` | Info | Existing | EXT (exists) |
| `prefix` | Per-guild prefix | Existing | EXT (exists) |
| `settings` / `disable` | Guild config | Existing config commands | EXT (exists) |
| `poll` / `remind` | Utility | Existing | EXT (exists) |
| `stats` / `invite` | Bot info | `/health`, `/invites` | EXT (exists) |

## 3. Phase plan

### Phase 1 — RPG core + economy verbs (this change)

Deliverables:

- `bot/models/rpg.py`: profiles, inventory, cooldowns, quests.
- `bot/repositories/rpg.py`: all persistence behind an injectable repository.
- `bot/services/rpg_content.py`: data-driven Minecraft content catalogue (biomes,
  mobs, weapons, pets, crates, shop, quests, rarities).
- `bot/services/rpg.py`: hunt, battle (mob + PvP), zoo, pets, equip, inventory,
  crates, sell, shop/buy, quests, profile, leaderboard.
- `bot/commands/rpg.py`: `/rpg` group + flat prefix aliases.
- `bot/commands/economy.py`: `/economy` group + flat prefix aliases.
- Alembic `0031_minecraft_rpg`.
- Unit tests for content, service, repository contracts, command registration.
- Wire `EconomyService` and `RpgService` into `Bot`; fix wallet/balance drift.

### Phase 2 — Depth

- `use` consumables, `sacrifice`, badges/titles/bio, blackjack, roulette, guess,
  hangman, connect4, lottery.
- Quest shop and weekly quests.
- Rank cards / profile rendering.

### Phase 3 — Social & multiplayer economy

- Marriage/family/ship, reputation, bazaar, trade, teams, duels, tournaments.
- Player-market persistence and anti-abuse limits.

### Phase 4 — Hardening & parity verification

- Live-guild manual test matrix for every command.
- Load/cooldown abuse tests.
- Help-category coverage assertions (no advertised-but-unregistered commands).
- Documentation and changelog.

## 4. Phase 1 data model

| Table | Purpose |
|---|---|
| `rpg_profiles` | Level, XP, health, attack, defense, equipped weapon/pet, biome, counters |
| `rpg_inventory` | Owned mobs, weapons, pets, crates, materials (stacked by key) |
| `rpg_cooldowns` | Per-user per-action ready timestamp |
| `rpg_quests` | Daily quest assignment, progress, completion, claim state |

Design notes:

- Coins remain in the existing `economy` table (`wallet`). RPG never invents a
  second currency.
- Item keys reference the static catalogue, so content can be rebalanced without
  a migration.
- All writes use `INSERT … ON CONFLICT` + row locks where the existing repository
  does, preserving the repo's concurrency pattern.
- Unique constraints: `(guild_id, user_id)` for profiles; `(guild_id, user_id,
  item_key)` for inventory; `(guild_id, user_id, action)` for cooldowns;
  `(guild_id, user_id, quest_key, day)` for quests.

## 5. Testing strategy

- **Content tests:** every biome references real mobs; every crate drop references
  a real item; every shop item references a real item; rarity weights sum sanely.
- **Service tests:** injected fake repository + seeded RNG prove cooldowns, hunt
  outcomes, level-ups, battle resolution, crate rolls, quest progress/claim,
  equip validation, sell math, and insufficient-funds handling.
- **Registration tests:** extension imports, `setup()` adds the cog, no duplicate
  root command names, no forbidden `ctx` option.
- **Regression:** existing suite must stay green; no database reset.

## 6. Non-goals / explicit exclusions

- No copying of OwO response strings, images, or command implementation.
- No copyrighted Minecraft assets; emoji and text only, original names/descriptions.
- No real-money, crypto, or gambling-to-currency conversion.
- No dashboard work (still deferred by project policy).

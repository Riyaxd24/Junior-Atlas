import random
from dataclasses import dataclass


class TicTacToeEngine:
    def __init__(self):
        self.board = [[0, 0, 0] for _ in range(3)]

    def move(self, row, column, player):
        if not 0 <= row < 3 or not 0 <= column < 3:
            raise ValueError("Illegal move.")
        if player not in (1, 2):
            raise ValueError("Illegal player.")
        if self.board[row][column] != 0:
            raise ValueError("Square is already occupied.")
        self.board[row][column] = player
        return self.check_winner()

    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        for column in range(3):
            if self.board[0][column] == self.board[1][column] == self.board[2][column] != 0:
                return self.board[0][column]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]
        if all(cell != 0 for row in self.board for cell in row):
            return 0
        return None


class RPSEngine:
    CHOICES = ("rock", "paper", "scissors")

    @classmethod
    def winner(cls, player1_choice, player2_choice):
        if player1_choice not in cls.CHOICES or player2_choice not in cls.CHOICES:
            raise ValueError("Illegal choice.")
        if player1_choice == player2_choice:
            return 0
        beats = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper",
        }
        return 1 if beats[player1_choice] == player2_choice else 2


TRIVIA_QUESTIONS = (
    ("Which data structure uses LIFO?", ("Stack", "Queue", "Tree", "Map"), "Stack"),
    ("What is the capital of Australia?", ("Sydney", "Melbourne", "Canberra", "Brisbane"), "Canberra"),
    ("Which planet is known as the Red Planet?", ("Mars", "Venus", "Jupiter", "Mercury"), "Mars"),
)


class TriviaEngine:
    def __init__(self):
        question, options, answer = random.choice(TRIVIA_QUESTIONS)
        self.question = question
        self.options = list(options)
        self.answer = answer

    def correct(self, answer):
        return answer == self.answer


# ---------------------------------------------------------------------------
# UNO
# ---------------------------------------------------------------------------
UNO_COLORS = ("red", "yellow", "green", "blue")
UNO_ACTION_VALUES = ("skip", "reverse", "draw2")
UNO_LABELS = {
    "skip": "🚫",
    "reverse": "🔄",
    "draw2": "+2",
    "wild": "🌈",
    "wild_draw4": "🃏",
}


@dataclass(frozen=True)
class UnoCard:
    color: str
    value: str

    @property
    def label(self) -> str:
        if self.color == "wild":
            return f"{UNO_LABELS[self.value]} Wild"
        symbol = UNO_LABELS.get(self.value, self.value)
        return f"{symbol} {self.color.title()}"

    def to_dict(self):
        return {"color": self.color, "value": self.value}

    @classmethod
    def from_dict(cls, data):
        return cls(str(data["color"]), str(data["value"]))


def build_uno_deck(rng=None):
    rng = rng or random
    deck = []
    for color in UNO_COLORS:
        deck.append(UnoCard(color, "0"))
        for number in range(1, 10):
            deck.extend((UnoCard(color, str(number)), UnoCard(color, str(number))))
        for value in UNO_ACTION_VALUES:
            deck.extend((UnoCard(color, value), UnoCard(color, value)))
    for _ in range(4):
        deck.append(UnoCard("wild", "wild"))
        deck.append(UnoCard("wild", "wild_draw4"))
    rng.shuffle(deck)
    return deck


@dataclass
class UnoResult:
    event: str
    message: str
    player_id: int
    next_player_id: int | None = None
    winner_id: int | None = None
    card: UnoCard | None = None
    game_over: bool = False


class UnoEngine:
    """Deterministic, self-contained UNO rules engine.

    The engine owns all validation (turn order, playability, wild colours,
    draw pile exhaustion) so the Discord view cannot create an illegal state.
    """

    MIN_PLAYERS = 2
    MAX_PLAYERS = 6
    STARTING_HAND = 7

    def __init__(self, player_ids, rng=None):
        players = list(dict.fromkeys(int(player_id) for player_id in player_ids))
        if not self.MIN_PLAYERS <= len(players) <= self.MAX_PLAYERS:
            raise ValueError(
                f"UNO requires between {self.MIN_PLAYERS} and {self.MAX_PLAYERS} players."
            )
        self.player_ids = tuple(players)
        self.rng = rng or random.Random()
        self.hands = {player_id: [] for player_id in self.player_ids}
        self.draw_pile = []
        self.discard = []
        self.direction = 1
        self.turn_index = 0
        self.current_color = None
        self.started = False
        self.winner_id = None

    # ------------------------------------------------------------- lifecycle
    def start(self):
        self.draw_pile = build_uno_deck(self.rng)
        for _ in range(self.STARTING_HAND):
            for player_id in self.player_ids:
                self.hands[player_id].append(self.draw_pile.pop())
        while True:
            card = self.draw_pile.pop()
            if card.color != "wild":
                self.discard.append(card)
                self.current_color = card.color
                break
            self.draw_pile.insert(0, card)
        # Apply the first card's action to the starting player.
        self.started = True
        self._apply_starting_action()
        return self

    def _apply_starting_action(self):
        value = self.top.value
        if value == "skip":
            self._advance()
        elif value == "reverse":
            if len(self.player_ids) == 2:
                self._advance()
            else:
                self.direction = -1
        elif value == "draw2":
            target = self._peek_next()
            self._give_cards(target, 2)
            self._advance()

    # ------------------------------------------------------------- accessors
    @property
    def top(self):
        return self.discard[-1]

    def current_player(self):
        return self.player_ids[self.turn_index]

    def hand(self, player_id):
        return list(self.hands.get(int(player_id), ()))

    def can_play(self, card):
        if card.color == "wild":
            return True
        return card.color == self.current_color or card.value == self.top.value

    def has_playable(self, player_id):
        return any(self.can_play(card) for card in self.hands[int(player_id)])

    def _next_index(self, steps=1):
        count = len(self.player_ids)
        return (self.turn_index + self.direction * steps) % count

    def _peek_next(self):
        return self.player_ids[self._next_index()]

    def _advance(self, steps=1):
        self.turn_index = self._next_index(steps)

    # ------------------------------------------------------------- play
    def play(self, player_id, card_index, chosen_color=None):
        if not self.started:
            raise ValueError("The game has not started.")
        if self.winner_id is not None:
            raise ValueError("The game is already over.")
        player_id = int(player_id)
        if player_id != self.current_player():
            raise ValueError("It is not your turn.")
        hand = self.hands[player_id]
        if not isinstance(card_index, int) or not 0 <= card_index < len(hand):
            raise ValueError("That card is not in your hand.")
        card = hand[card_index]
        if not self.can_play(card):
            raise ValueError("That card cannot be played on the current discard.")
        if card.color == "wild" and chosen_color not in UNO_COLORS:
            raise ValueError("Choose red, yellow, green, or blue for a wild card.")

        hand.pop(card_index)
        self.discard.append(card)
        self.current_color = chosen_color if card.color == "wild" else card.color

        if not hand:
            self.winner_id = player_id
            return UnoResult(
                event="win",
                message=f"<@{player_id}> played their last card and won!",
                player_id=player_id,
                winner_id=player_id,
                card=card,
                game_over=True,
            )

        extra = ""
        advances = 1
        if card.value == "skip":
            skipped = self._peek_next()
            advances = 2
            extra = f" <@{skipped}> is skipped."
        elif card.value == "reverse":
            if len(self.player_ids) == 2:
                advances = 0
                extra = " The reverse acts as a skip in a two-player game."
            else:
                self.direction *= -1
                extra = " Play direction reversed."
        elif card.value in {"draw2", "wild_draw4"}:
            amount = 2 if card.value == "draw2" else 4
            target = self._peek_next()
            self._give_cards(target, amount)
            advances = 2
            extra = f" <@{target}> draws {amount} and is skipped."
        elif card.color == "wild":
            extra = f" Colour changed to **{self.current_color}**."

        for _ in range(advances):
            self._advance()

        return UnoResult(
            event="play",
            message=f"<@{player_id}> played **{card.label}**.{extra}",
            player_id=player_id,
            next_player_id=self.current_player(),
            card=card,
        )

    def draw(self, player_id):
        if not self.started:
            raise ValueError("The game has not started.")
        if self.winner_id is not None:
            raise ValueError("The game is already over.")
        player_id = int(player_id)
        if player_id != self.current_player():
            raise ValueError("It is not your turn.")
        card = self._draw_one()
        if card is None:
            raise ValueError("There are no cards left to draw.")
        self.hands[player_id].append(card)
        self._advance()
        return UnoResult(
            event="draw",
            message=f"<@{player_id}> drew a card.",
            player_id=player_id,
            next_player_id=self.current_player(),
            card=card,
        )

    # ------------------------------------------------------------- deck
    def _draw_one(self):
        if not self.draw_pile:
            if len(self.discard) <= 1:
                return None
            top = self.discard.pop()
            remainder = self.discard
            self.discard = [top]
            self.draw_pile = remainder
            self.rng.shuffle(self.draw_pile)
        return self.draw_pile.pop() if self.draw_pile else None

    def _give_cards(self, player_id, amount):
        for _ in range(amount):
            card = self._draw_one()
            if card is None:
                break
            self.hands[player_id].append(card)

    # ------------------------------------------------------------- persistence
    def to_dict(self):
        return {
            "player_ids": list(self.player_ids),
            "hands": {str(key): [card.to_dict() for card in hand] for key, hand in self.hands.items()},
            "draw_pile": [card.to_dict() for card in self.draw_pile],
            "discard": [card.to_dict() for card in self.discard],
            "direction": self.direction,
            "turn_index": self.turn_index,
            "current_color": self.current_color,
            "started": self.started,
            "winner_id": self.winner_id,
        }

    @classmethod
    def from_dict(cls, data):
        engine = cls.__new__(cls)
        engine.rng = random.Random()
        engine.player_ids = tuple(int(value) for value in data["player_ids"])
        engine.hands = {
            int(key): [UnoCard.from_dict(card) for card in cards]
            for key, cards in data["hands"].items()
        }
        engine.draw_pile = [UnoCard.from_dict(card) for card in data["draw_pile"]]
        engine.discard = [UnoCard.from_dict(card) for card in data["discard"]]
        engine.direction = int(data.get("direction", 1))
        engine.turn_index = int(data.get("turn_index", 0))
        engine.current_color = data.get("current_color")
        engine.started = bool(data.get("started", True))
        engine.winner_id = data.get("winner_id")
        return engine


# ---------------------------------------------------------------------------
# Hand Cricket
# ---------------------------------------------------------------------------
@dataclass
class CricketResult:
    event: str
    message: str
    striker_id: int
    bowler_id: int
    runs: int = 0
    out: bool = False
    ball_complete: bool = False
    innings_over: bool = False
    game_over: bool = False
    winner_id: int | None = None
    scores: dict | None = None
    target: int | None = None
    balls_left: int | None = None


class HandCricketEngine:
    """Two-player hand cricket with two innings and one wicket per innings.

    Each delivery is resolved only when both the striker and bowler have chosen
    a number from 1 to 6. Equal numbers dismiss the striker; otherwise the
    striker scores their own number.
    """

    def __init__(self, player1_id, player2_id, overs=1, rng=None):
        player1_id, player2_id = int(player1_id), int(player2_id)
        if player1_id == player2_id:
            raise ValueError("Hand Cricket requires two different players.")
        if not 1 <= int(overs) <= 50:
            raise ValueError("Overs must be between 1 and 50.")
        self.player_ids = (player1_id, player2_id)
        self.overs = int(overs)
        self.balls_per_innings = self.overs * 6
        self.rng = rng or random.Random()
        self.innings = 1
        self.scores = {player1_id: 0, player2_id: 0}
        self.balls = 0
        self.picks = {}
        self.target = None
        self.winner_id = None
        self.game_over = False

    # ------------------------------------------------------------- roles
    @property
    def striker_id(self):
        return self.player_ids[0] if self.innings == 1 else self.player_ids[1]

    @property
    def bowler_id(self):
        return self.player_ids[1] if self.innings == 1 else self.player_ids[0]

    @property
    def balls_left(self):
        return max(0, self.balls_per_innings - self.balls)

    def submit(self, player_id, number):
        player_id = int(player_id)
        if self.game_over:
            raise ValueError("The match is already over.")
        if player_id not in self.player_ids:
            raise ValueError("You are not part of this match.")
        if not isinstance(number, int) or not 1 <= number <= 6:
            raise ValueError("Choose a number from 1 to 6.")
        if player_id in self.picks:
            raise ValueError("You already chose a number for this ball.")
        self.picks[player_id] = number

        if set(self.picks) != set(self.player_ids):
            waiting = self.player_ids[0] if self.player_ids[1] in self.picks else self.player_ids[1]
            return CricketResult(
                event="waiting",
                message=f"<@{player_id}> is ready. Waiting for <@{waiting}>.",
                striker_id=self.striker_id,
                bowler_id=self.bowler_id,
                scores=dict(self.scores),
                target=self.target,
                balls_left=self.balls_left,
            )

        striker = self.striker_id
        bowler = self.bowler_id
        striker_choice = self.picks[striker]
        bowler_choice = self.picks[bowler]
        self.picks.clear()
        self.balls += 1
        runs = 0
        out = striker_choice == bowler_choice
        if not out:
            runs = striker_choice
            self.scores[striker] += runs

        innings_ended = out or self.balls >= self.balls_per_innings
        game_over = False
        reached_target = (
            self.innings == 2
            and self.target is not None
            and self.scores[striker] >= self.target
        )
        if reached_target:
            innings_ended = True
            game_over = True
        elif innings_ended and self.innings == 2:
            game_over = True

        target = self.target
        winner = None
        if game_over:
            first, second = self.player_ids
            if self.scores[first] > self.scores[second]:
                winner = first
            elif self.scores[second] > self.scores[first]:
                winner = second
            else:
                winner = 0
            self.winner_id = winner
            self.game_over = True

        parts = []
        if out:
            parts.append(
                f"<@{striker}> chose **{striker_choice}** and <@{bowler}> "
                f"chose **{bowler_choice}** — OUT!"
            )
        else:
            parts.append(
                f"<@{striker}> scored **{runs}** "
                f"(chose {striker_choice}, bowler chose {bowler_choice})."
            )
        parts.append(
            f"Score: <@{self.player_ids[0]}> {self.scores[self.player_ids[0]]} · "
            f"<@{self.player_ids[1]}> {self.scores[self.player_ids[1]]}"
        )

        if not game_over and innings_ended:
            # First innings is complete: the second player now bats with a
            # target of first-innings score + 1.
            self.innings = 2
            self.balls = 0
            self.target = self.scores[self.player_ids[0]] + 1
            target = self.target
            parts.append(
                f"Innings over. <@{self.player_ids[1]}> needs "
                f"**{self.target}** runs to win from {self.balls_per_innings} balls."
            )

        if game_over:
            if winner == 0:
                parts.append("The match is tied!")
            else:
                parts.append(f"<@{winner}> wins the match!")

        if game_over or innings_ended:
            balls_left_value = 0
        else:
            balls_left_value = self.balls_left

        return CricketResult(
            event="game_over" if game_over else ("innings" if innings_ended else "ball"),
            message=" ".join(parts),
            striker_id=striker,
            bowler_id=bowler,
            runs=runs,
            out=out,
            ball_complete=True,
            innings_over=innings_ended,
            game_over=game_over,
            winner_id=winner,
            scores=dict(self.scores),
            target=target,
            balls_left=balls_left_value,
        )

    def to_dict(self):
        return {
            "player_ids": list(self.player_ids),
            "overs": self.overs,
            "innings": self.innings,
            "scores": {str(key): value for key, value in self.scores.items()},
            "balls": self.balls,
            "picks": {str(key): value for key, value in self.picks.items()},
            "target": self.target,
            "winner_id": self.winner_id,
            "game_over": self.game_over,
        }

    @classmethod
    def from_dict(cls, data):
        engine = cls(
            int(data["player_ids"][0]),
            int(data["player_ids"][1]),
            overs=int(data.get("overs", 1)),
        )
        engine.innings = int(data.get("innings", 1))
        engine.scores = {int(key): int(value) for key, value in data["scores"].items()}
        engine.balls = int(data.get("balls", 0))
        engine.picks = {int(key): int(value) for key, value in data.get("picks", {}).items()}
        engine.target = data.get("target")
        engine.winner_id = data.get("winner_id")
        engine.game_over = bool(data.get("game_over", False))
        return engine

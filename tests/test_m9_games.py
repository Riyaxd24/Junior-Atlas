import pytest

from bot.services.games import RPSEngine, TicTacToeEngine, TriviaEngine


def test_tictactoe_winner_and_illegal_moves():
    engine = TicTacToeEngine()
    assert engine.move(0, 0, 1) is None
    assert engine.move(1, 0, 2) is None
    assert engine.move(0, 1, 1) is None
    assert engine.move(1, 1, 2) is None
    assert engine.move(0, 2, 1) == 1

    with pytest.raises(ValueError):
        engine.move(0, 2, 2)
    with pytest.raises(ValueError):
        engine.move(-1, 0, 1)


def test_tictactoe_draw():
    engine = TicTacToeEngine()
    sequence = (
        (0, 0, 1), (0, 1, 2), (0, 2, 1),
        (1, 1, 2), (1, 0, 1), (1, 2, 2),
        (2, 1, 1), (2, 0, 2), (2, 2, 1),
    )
    result = None
    for row, column, player in sequence:
        result = engine.move(row, column, player)
    assert result == 0


@pytest.mark.parametrize(
    ("player1", "player2", "winner"),
    [
        ("rock", "scissors", 1),
        ("rock", "paper", 2),
        ("scissors", "scissors", 0),
        ("paper", "rock", 1),
    ],
)
def test_rps_winner(player1, player2, winner):
    assert RPSEngine.winner(player1, player2) == winner


def test_trivia_answer_is_exact():
    trivia = TriviaEngine()
    assert trivia.correct(trivia.answer) is True

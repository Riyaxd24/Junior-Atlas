import random


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

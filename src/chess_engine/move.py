from chess_engine import Board

class moveGenerator():
    def __init__(self, board: Board):
        self.board = board

    def generate_moves(self):
        
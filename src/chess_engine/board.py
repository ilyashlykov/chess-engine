import numpy as np

fen = str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
class Board:
    def __init__(self, fen):
        positions, self.turn, self.castling, self.en_passant, self.halfmove_clock, self.fullmove_number = fen.split(' ')
        self.board = np.zeros(64, dtype=object)
        index = 0
        for rows in positions.split('/'):
            for symbol in rows:
                if symbol.isdigit():
                    if int(symbol) > 1:
                        self.board[index:index + int(symbol)] = None
                        index += int(symbol)
                    else:
                        self.board[index] = None
                        index += 1
                else:
                    self.board[index] = symbol
                    index += 1

    def get_position(self):
        return self.position


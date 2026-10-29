import numpy as np

fen = str("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
files = 'abcdefgh'
class Board:
    def __init__(self, fen):
        positions, self.turn, self.castling, self.en_passant, self.halfmove_clock, self.fullmove_number = fen.split(' ')
        self.board = np.zeros(64, dtype=object)
        index = 0
        self.piece_bitboards = {
            'p': "Bpawns",
            'r': "Brooks",
            'n': "Bknights",
            'b': "Bbishops",
            'q': "Bqueen",
            'k': "Bking",
            'K': "Wking",
            'Q': "Wqueen",
            'B': "Wbishops",
            'N': "Wknights",
            'R': "Wrooks",
            'P': "Wpawns"
        }

        for rows in positions.split('/')[-1::-1]:
            if len(rows) > 8:
                print("Position pasrsing error")
            for symbol in rows:
                if symbol.isdigit():
                    if int(symbol) >= 1:
                        self.board[index:index + int(symbol)] = None
                        index += int(symbol)
                else:
                    self.board[index] = symbol
                    index += 1

        self.Bpawns, self.Brooks, self.Bknights, self.Bbishops, self.Bqueen, self.Bking,\
        self.Wpawns, self.Wrooks, self.Wknights, self.Wbishops, self.Wqueen, self.Wking = np.zeros(12, dtype=int)

        self.Bpawns = sum(1 << i for i,is_piece in enumerate((self.board == 'p')) if is_piece)
        self.Brooks = sum(1 << i for i,is_piece in enumerate((self.board == 'r')) if is_piece)
        self.Bknights = sum(1 << i for i,is_piece in enumerate((self.board == 'n')) if is_piece)
        self.Bbishops = sum(1 << i for i,is_piece in enumerate((self.board == 'b')) if is_piece)
        self.Bqueen = sum(1 << i for i,is_piece in enumerate((self.board == 'q')) if is_piece)
        self.Bking = sum(1 << i for i,is_piece in enumerate((self.board == 'k')) if is_piece)

        self.Wpawns = sum(1 << i for i,is_piece in enumerate((self.board == 'P')) if is_piece)
        self.Wrooks = sum(1 << i for i,is_piece in enumerate((self.board == 'R')) if is_piece)
        self.Wknights = sum(1 << i for i,is_piece in enumerate((self.board == 'N')) if is_piece)
        self.Wbishops = sum(1 << i for i,is_piece in enumerate((self.board == 'B')) if is_piece)
        self.Wqueen = sum(1 << i for i,is_piece in enumerate((self.board == 'Q')) if is_piece)
        self.Wking = sum(1 << i for i,is_piece in enumerate((self.board == 'K')) if is_piece)

    def __str__(self):
        board_str = ""
        for i in range(8):
            row = [j if j is not None else '.'for j in self.board[-(i+1)*8: -i*8 - 1]]
            board_str += " ".join(row) + "\n"
        return board_str

    @property
    def white_occupancy(self):
        return (self.Wknights | self.Wpawns | self.Wrooks | self.Wbishops | self.Wqueen | self.Wking)

    @property
    def black_occupancy(self):
        return (self.Bknights | self.Bpawns | self.Brooks | self.Bbishops | self.Bqueen | self.Bking)

    def index_to_square(self, index: int) -> str | None:
        if 0 <= index < 64:
            rank = index//8 + 1
            file = files[index%8]
            return file + str(rank)
        else:
            return None

    def check_board_square(self, pos: int) -> int:
        if 0 <= pos < 64:
            mask = 1 << pos
            for attr_name in self.piece_bitboards.values():
                if getattr(self, attr_name) & mask:
                    return True
            return False
        else:
            return False

    def get_piece(self, pos: int) -> str | None:
        mask = 1 << pos
        for piece, attr_name in self.piece_bitboards.items():
            bitboard = getattr(self, attr_name)
            if bitboard & mask:
                return piece
        return None

    def get_piece_positions(self, bitboard: int) -> list[int]:
        index = 0
        position = []
        while index < 64:
            mask = 1 << index
            if bitboard & mask:
                position.append(index)
            index += 1
        return position

    def generate_knight_moves(self, Kn: int, own_pieces: int):
        nA = sum(1 << i for i in range(0, 64, 8))
        nH = sum(1 << i for i in range(7, 64, 8))
        nAB = sum(1 << i for i in range(1, 64, 8)) | nA
        nGH = sum(1 << i for i in range(6, 64, 8)) | nH
        moves_bits = ~nA  & (Kn << 17 | Kn >> 15)\
                   | ~nH  & (Kn >> 17 | Kn << 15)\
                   | ~nAB & (Kn << 10 | Kn >> 6)\
                   | ~nGH & (Kn << 6  | Kn >> 10)
        return moves_bits & ~own_pieces

    def generate_sliding_moves(self, piece_bitboard, directions, own_pieces, occupied) -> int:
        moves = 0
        for position in self.get_piece_positions(piece_bitboard):
            pos_file = position%8
            pos_rank = position//8
            for delta_file, delta_rank in directions:
                file = delta_file + pos_file
                rank = delta_rank + pos_rank

                while 0 <= file < 8 and 0 <= rank < 8:
                    target = rank*8 + file
                    target_mask = 1 << target
                    if target_mask & own_pieces:
                        break

                    moves |= target_mask

                    if target_mask & occupied:
                        break

                    file += delta_file
                    rank += delta_rank
        return moves

    def generate_bishop_moves(self, bishops, own_pieces, occupied):
        directions = [(-1, 1), (-1, -1), (1, -1), (1, 1)]
        return self.generate_sliding_moves(bishops, directions, own_pieces, occupied)

    def generate_rook_moves(self, rooks, own_pieces, occupied):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self.generate_sliding_moves(rooks, directions, own_pieces, occupied)

    def generate_queen_moves(self, queen, own_pieces, occupied):
        directions = [(-1, 1), (-1, -1), (1, -1), (1, 1), (1, 0), (-1, 0), (0, -1), (0, 1)]
        return self.generate_sliding_moves(queen, directions, own_pieces, occupied)

    def generate_king_moves(self, king, own_pieces, occupied):
        moves = 0
        directions = [(-1, 1), (-1, -1), (1, -1), (1, 1), (1, 0), (-1, 0), (0, -1), (0, 1)]
        for delta_file, delta_rank in directions:
            target = self.get_piece_positions(king)[0] + delta_rank*8 + delta_file
            target_mask = 1 << target
            if (target_mask & ~own_pieces) or (target_mask & occupied):
                moves |= target_mask
        return moves

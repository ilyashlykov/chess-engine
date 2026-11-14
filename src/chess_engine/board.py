import numpy as np
from chess_engine.move import Move
from copy import deepcopy

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
                print("Position parsing error")
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

    def square_to_index(self, square: str) -> int | None:
        if square != '-':
            file, rank = square
            index = files.find(file) + (int(rank) - 1)*8 
            return index
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
        k_rank, k_file = self.get_piece_positions(king)[0] // 8, self.get_piece_positions(king)[0] % 8
        for delta_file, delta_rank in directions:
            if not (0 <= k_rank + delta_rank < 8) or not (0 <= k_file + delta_file < 8):
                continue
            target = self.get_piece_positions(king)[0] + delta_rank*8 + delta_file
            if target < 0:
                continue
            target_mask = 1 << target
            if (target_mask & ~own_pieces) or (target_mask & occupied):
                moves |= target_mask
        if self.turn == 'w':
            white_king_attacked = self.is_square_attacked(king, 'b', True)
            if (self.white_occupancy | self.black_occupancy) & 0b1110 == 0 and 'Q' in self.castling and white_king_attacked:
                moves |= 0b100
            if (self.white_occupancy | self.black_occupancy) & 0b1100000 == 0 and 'K' in self.castling and white_king_attacked:
                moves |= 0b1000000
        if self.turn == 'b':
            black_king_attacked = self.is_square_attacked(king, 'w', True)
            if (self.white_occupancy | self.black_occupancy) & 0b1110 << 56 == 0 and 'q' in self.castling and black_king_attacked:
                moves |= 0b100 << 56
            if (self.white_occupancy | self.black_occupancy) & 0b1100000 << 56 == 0 and 'k' in self.castling and black_king_attacked:
                moves |= 0b1000000 << 56
        return moves

    def generate_pawn_moves(self, pawns, own_pieces, occupied, color):
        moves = 0
        rA = sum(1 << i for i in range(0, 64, 8))
        rH = sum(1 << i for i in range(7, 64, 8))
        BOARD_MASK = (1 << 64) - 1
        RANK_3 = 0b11111111 << 16
        RANK_6 = 0b11111111 << 40
        occupied_all = own_pieces | occupied
        ep_square = self.square_to_index(self.en_passant)
        en_passant_index = 1 << ep_square if ep_square else 0
        if color == 'w':
            one_step = ((pawns << 8) & BOARD_MASK) & ~occupied_all
            two_step = ((one_step & RANK_3) << 8) & ~occupied_all
            attacks = (((pawns & ~rH) << 9) | ((pawns & ~rA) << 7)) & occupied
            en_passant_move = ((en_passant_index >> 7) | (en_passant_index >> 9)) & pawns
        else:
            one_step = (pawns >> 8) & ~occupied_all
            two_step = ((one_step & RANK_6) >> 8) & ~occupied_all
            attacks = (((pawns & ~rA) >> 9) | ((pawns & ~rH) >> 7)) & occupied
            en_passant_move = ((en_passant_index << 7) | (en_passant_index << 9)) & pawns
        if en_passant_move:
            moves |= en_passant_index
        moves |= one_step | two_step | attacks
        return moves

    def get_moves_from_board(self, piece, pos):
        moves = 0
        if piece == 'r':
            moves = self.generate_rook_moves(1<<pos, self.black_occupancy, self.white_occupancy)
        elif piece == 'R':
            moves = self.generate_rook_moves(1<<pos, self.white_occupancy, self.black_occupancy)
        elif piece == 'n':
            moves = self.generate_knight_moves(1<<pos, self.black_occupancy)
        elif piece == 'N':
            moves = self.generate_knight_moves(1<<pos, self.white_occupancy)
        elif piece == 'b':
            moves = self.generate_bishop_moves(1<<pos, self.black_occupancy, self.white_occupancy)
        elif piece == 'B':
            moves = self.generate_bishop_moves(1<<pos, self.white_occupancy, self.black_occupancy)
        elif piece == 'q':
            moves = self.generate_queen_moves(1<<pos, self.black_occupancy, self.white_occupancy)
        elif piece == 'Q':
            moves = self.generate_queen_moves(1<<pos, self.white_occupancy, self.black_occupancy)
        elif piece == 'k':
            moves = self.generate_king_moves(1<<pos, self.black_occupancy, self.white_occupancy)
        elif piece == 'K':
            moves = self.generate_king_moves(1<<pos, self.white_occupancy, self.black_occupancy)
        elif piece == 'p':
            moves = self.generate_pawn_moves(1<<pos, self.black_occupancy, self.white_occupancy, 'b')
        elif piece == 'P':
            moves = self.generate_pawn_moves(1<<pos, self.white_occupancy, self.black_occupancy, 'w')
        return moves

    def get_move_list_from_board(self, piece, pos):
        targets = self.get_piece_positions(
            self.get_moves_from_board(piece, pos)
        )

        moves = []
        promotion_rank = 7 if piece.isupper() else 0

        for to_sq in targets:
            if piece.lower() == 'p' and to_sq // 8 == promotion_rank:
                moves.extend(
                    Move(pos, to_sq, promotion=choice)
                    for choice in ('q', 'r', 'b', 'n')
                )
            else:
                moves.append(Move(pos, to_sq))

        return moves

    def get_legal_move_list(self, piece, pos):
        moves = self.get_move_list_from_board(piece, pos)
        legal_moves = []
        for move in moves:
            test_board = deepcopy(self)
            king_bitboard = "Wking" if self.turn == 'w' else "Bking"
            if not test_board.make_move(move) or not test_board.is_square_attacked(1 << (getattr(test_board, king_bitboard).bit_length() - 1)): # test_board.get_legal_moves():
                continue 

            legal_moves.append(move)
        return legal_moves


    def check_en_passaunt(self, piece, from_sq, to_sq):
        if piece.lower() != 'p' or abs(from_sq - to_sq) != 16:
            self.en_passant = '-'
            return
        self.en_passant = self.index_to_square(abs(from_sq + to_sq) // 2)

    def check_castling(self, piece):
        if piece == 'R':
            if not (self.Wrooks & (1 << 0)):
                self.castling = self.castling.replace('Q', '')
            if not (self.Wrooks & (1 << 7)):
                self.castling = self.castling.replace('K', '')
        if piece == 'r':
            if ~ (self.Brooks & (1 << 56)):
                self.castling = self.castling.replace('q', '')
            if ~ (self.Brooks & (1 << 63)):
                self.castling = self.castling.replace('k', '')
        if piece == 'K':
            self.castling = self.castling.replace('K', '')
            self.castling = self.castling.replace('Q', '')
        if piece == 'k':
            self.castling = self.castling.replace('k', '')
            self.castling = self.castling.replace('q', '')
        if self.castling == '':
            self.castling = '-'

    def make_castle(self, move: Move):
        from_sq = move.from_sq
        to_sq = move.to_sq
        new_pos = (from_sq + to_sq) // 2
        if self.turn == 'w':
            rook_pos = 0 if to_sq == 2 else 7
            self.Wrooks = (self.Wrooks & ~(1 << rook_pos)) | 1 << new_pos
            self.board[new_pos] = 'R'
            self.board[rook_pos] = None
        elif self.turn == 'b':
            rook_pos = 56 if to_sq == 58 else 63
            self.Brooks = (self.Brooks & ~(1 << rook_pos)) | 1 << new_pos
            self.board[new_pos] = 'r'
            self.board[rook_pos] = None

    def is_square_attacked(self, pos, turn = None, is_king = False):
        # pos = 1 << piece
        if turn is None:
            turn = self.turn
        if turn == 'b':
            pawns_moves = self.generate_pawn_moves(self.Bpawns, self.black_occupancy, self.white_occupancy, 'b')
            rooks_moves  = self.generate_rook_moves(self.Brooks, self.black_occupancy, self.white_occupancy)
            knights_moves = self.generate_knight_moves(self.Bknights, self.black_occupancy)
            bishops_moves = self.generate_bishop_moves(self.Bbishops, self.black_occupancy, self.white_occupancy)
            queen_moves = self.generate_queen_moves(self.Bqueen, self.black_occupancy, self.white_occupancy)
            black_moves = pawns_moves | rooks_moves | knights_moves | bishops_moves | queen_moves
            if not is_king:
                king_moves = self.generate_king_moves(self.Bking, self.black_occupancy, self.white_occupancy)
                black_moves |= king_moves
            if (black_moves & pos):
                return False
        elif turn == 'w':
            pawns_moves = self.generate_pawn_moves(self.Wpawns, self.white_occupancy, self.black_occupancy, 'w')
            rooks_moves  = self.generate_rook_moves(self.Wrooks, self.white_occupancy, self.black_occupancy)
            knights_moves = self.generate_knight_moves(self.Wknights, self.white_occupancy)
            bishops_moves = self.generate_bishop_moves(self.Wbishops, self.white_occupancy, self.black_occupancy)
            queen_moves = self.generate_queen_moves(self.Wqueen, self.white_occupancy, self.black_occupancy)
            white_moves = pawns_moves | rooks_moves | knights_moves | bishops_moves | queen_moves
            if not is_king:
                king_moves = self.generate_king_moves(self.Wking, self.white_occupancy, self.black_occupancy)
                white_moves |= king_moves
            if (white_moves & pos):
                return False
        return True


    def make_move(self, move: Move):
        from_sq = move.from_sq
        to_sq = move.to_sq
        piece = self.get_piece(from_sq)
        if piece is None:
            return False
        piece_color = 'w' if piece.isupper() else 'b'
        if piece_color != self.turn:
            return False 
        moves = self.get_moves_from_board(piece, from_sq)
        to_mask = 1 << to_sq
        if not moves & to_mask:
            return False

        to_piece = self.get_piece(to_sq)
        if to_piece is not None and piece.islower() == to_piece.islower():
            return False

        is_promotion = (
            (piece == 'P' and to_sq//8 == 7) or 
            (piece == 'p' and to_sq//8 == 0)
        )

        if is_promotion != (move.promotion is not None):
            return False
        
        if to_piece is not None:
            captured_attr = self.piece_bitboards[to_piece]
            captured_bitboard = getattr(self, captured_attr)
            setattr(self, captured_attr, captured_bitboard & ~to_mask)

        if is_promotion:
            new_piece = (move.promotion.upper() if piece == 'P' else move.promotion.lower())        
        else: 
            new_piece = piece
        
        if self.square_to_index(self.en_passant) == to_sq:
            if piece_color == 'b':
                en_passaunt_attr = "Wpawns"
                index = to_sq + 8
                setattr(self, en_passaunt_attr, self.Wpawns & ~( 1 << index))
            else:
                en_passaunt_attr = "Bpawns"
                index = to_sq - 8
                setattr(self, en_passaunt_attr, self.Bpawns & ~(1 << index))
            self.board[index] = None
        self.check_en_passaunt(piece, from_sq, to_sq)

        from_mask = 1 << from_sq
        moving_attr = self.piece_bitboards[piece]
        moving_bitboard = getattr(self, moving_attr)
        setattr(self, moving_attr, moving_bitboard & ~from_mask)

        attr = self.piece_bitboards[new_piece]
        bitboard = getattr(self, attr)    
        setattr(self, attr, (bitboard & ~from_mask) | to_mask)
        self.board[from_sq] = None 
        self.board[to_sq] = new_piece
        if piece.lower() == 'k' and abs(from_sq - to_sq) == 2:
            self.make_castle(move)
        self.turn = 'b' if self.turn == 'w' else 'w'
        if self.castling != '-':
            self.check_castling(piece)
        return True


board = Board(fen)

import pygame
import sys
from pathlib import Path
import numpy as np
from chess_engine.board import Board

#TODO Доделать превращение пешки - исправить графическое отображени
"""
Сделать рокировку, легальные ходы - проверка короля на чек 
"""

SQ_SIZE = 120
BOARD_SIZE = 8 * SQ_SIZE
ASSETS = Path(__file__).parent / ".." / "assets" / "pieces" / "alpha"
LIGHT = (240, 220, 200)
DARK = (50, 50, 50)
FPS = 60
INVERT = False
SYMBOL_TO_PIECE = {symbol: name for symbol, name in zip(["r", "n", "b", "q", "k", "p", "P", "R", "N", "B", "Q", "K"],
                                                        ["bR", "bN", "bB", "bQ", "bK", "bP", "wP", "wR", "wN", "wB", "wQ", "wK"])}

def load_pieces(scale: int) -> dict[str, pygame.Surface]:
    pieces = {}
    for name in ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]:
        image_path = ASSETS / f"{name}.svg"
        if image_path.exists():
            image = pygame.image.load(image_path).convert_alpha()
            image = pygame.transform.smoothscale(image, (scale, scale))
            pieces[name] = image
        else:
            print(f"Warning: Image file {image_path} not found.")
    return pieces

class ChessGUI:
    def __init__(self, board: Board):
        pygame.init()
        self.screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
        pygame.display.set_caption("Chess Engine")
        self.clock = pygame.time.Clock()
        self.pieces = load_pieces(SQ_SIZE)
        self.board = board
        self.selected_square = None
        self.dragging = False
        self.dragging_piece = None
        self.legal_moves = []
        self.pending_promotion = None
        self.running = True


    def draw_board(self, scale: int):
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(col * scale, row * scale, scale, scale)
                pygame.draw.rect(self.screen, DARK if ((row + col) % 2) != INVERT else LIGHT, rect)

    def draw_pieces(self):
        for pos, item in enumerate(self.board.board):
            if item is not None:
                key = SYMBOL_TO_PIECE[item]
                x,y = pos%8, 7 - pos//8
            else:
                continue
            if key in self.pieces and not (self.dragging and self.selected_square == pos):
                self.screen.blit(self.pieces[key], (x*SQ_SIZE, y*SQ_SIZE))

    def screen_to_index(self, screen_pos):
        x, y = screen_pos
        if (0 <= x < BOARD_SIZE) and (0 <= y < BOARD_SIZE):
            col = x // SQ_SIZE
            row = y // SQ_SIZE
            return (7 - row)*8 + col
        else:
            return None

    def draw_selection(self):
        if self.selected_square is None:
             return
        col = self.selected_square % 8 
        row = 7 - self.selected_square // 8
        rect = pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        pygame.draw.rect(self.screen, list(i + 50 for i in DARK) if ((row + col) % 2) != INVERT else list(i - 40 for i in LIGHT) , rect)
        
        
    def clear_selection(self):
        self.selected_square = None
        self.dragging = False
        self.dragging_piece = None
        self.pending_promotion = None
        self.legal_moves = []

    def select_piece(self, square):
        piece = self.board.get_piece(square)
        if piece is None or ('w' if piece.isupper() else 'b') != self.board.turn:
            self.clear_selection()
            return False

        self.selected_square = square
        self.dragging_piece = piece
        # self.legal_moves = self.board.get_piece_positions(
        #     self.board.get_moves_from_board(piece, square)
        # )
        self.legal_moves = self.board.get_move_list_from_board(piece, square)
        return True

    # def commit_selected_move(self, to_square):
    #     if self.selected_square is None:
    #         return False
    #     if not self.board.make_move(self.selected_square, to_square):
    #         return False
    #     self.clear_selection()
    #     return True

    def commit_selected_move(self, to_square):
        if self.selected_square is None:
            return False

        candidates = [
            move for move in self.legal_moves
            if move.to_sq == to_square
        ]

        if not candidates:
            return False

        promotions = [move for move in candidates if move.promotion is not None]
        if promotions:
            self.pending_promotion = promotions
            self.dragging = False
            self.dragging_piece = None

            return True

        if not self.board.make_move(candidates[0]):
            return False

        self.clear_selection()
        return True

    def handle_mouse_down(self, screen_pos):
        if self.pending_promotion is not None:
            return

        square = self.screen_to_index(screen_pos)
        if square is None:
            return 
        if self.selected_square is not None and not self.dragging and any(move.to_sq == square for move in self.legal_moves):
            self.commit_selected_move(square)
            return

        piece = self.board.get_piece(square)
        if piece is not None and ('w' if piece.isupper() else 'b') == self.board.turn:
            if self.select_piece(square):
                self.dragging = True
        elif self.selected_square is None:
            self.clear_selection()

    def handle_mouse_up(self, screen_pos):
        if not self.dragging:
            return

        square = self.screen_to_index(screen_pos)
        if square is not None and square != self.selected_square and any(move.to_sq == square for move in self.legal_moves):
            self.commit_selected_move(square)
        self.dragging = False
        self.dragging_piece = None

    def draw_move_targets(self):
        for pos in[move.to_sq for move in self.legal_moves]:
            col = pos % 8 
            row = 7 - pos // 8
            center = (col * SQ_SIZE + SQ_SIZE // 2, row * SQ_SIZE + SQ_SIZE // 2)
            pygame.draw.circle(self.screen, (100, 90, 80), center, SQ_SIZE // 10)

    def draw_dragged_piece(self):
        if not self.dragging or self.dragging_piece is None:
            return 
        key = SYMBOL_TO_PIECE[self.dragging_piece]
        image = self.pieces.get(key)
        if image is None:
            return 
        mouse_x, mouse_y = pygame.mouse.get_pos()
        w,h = image.get_width(), image.get_height()
        scaled_piece = pygame.transform.smoothscale(image, (int(w*1.1), int(h*1.1)))
        self.screen.blit(scaled_piece, (mouse_x - SQ_SIZE//2, mouse_y - SQ_SIZE//2))

    def draw(self):
        self.draw_board(SQ_SIZE)
        self.draw_selection()
        self.draw_pieces()
        self.draw_move_targets()
        self.draw_dragged_piece()
        self.draw_promotion()

    def handle_promotion_click(self, screen_pos):
        if self.pending_promotion is None:
            return False

        x, y = screen_pos
        col = self.pending_promotion[0].to_sq % 8
        if not (col * SQ_SIZE <= x < (col + 1) * SQ_SIZE and ((0 <= y < 4 * SQ_SIZE and self.board.turn == 'w') or (3 < y <= 7 * SQ_SIZE and self.board.turn == 'b'))):
            return False

        choice_index = y // SQ_SIZE if self.board.turn == 'w' else 7 - y // SQ_SIZE
        choice = ('qrnb' if self.board.turn == 'b' else 'QRNB')[choice_index].lower()
        selected_move = next(
            (move for move in self.pending_promotion if move.promotion == choice),
            None,
        )
        if selected_move is None or not self.board.make_move(selected_move):
            return False

        self.clear_selection()
        return True

    def draw_promotion(self):
        if self.pending_promotion is None:
            return
        col = self.pending_promotion[0].to_sq % 8
        for i, key in enumerate('qrnb' if self.board.turn == 'b' else 'QRNB'):
            piece = SYMBOL_TO_PIECE[key]
            image = self.pieces[piece]
            row = i if self.board.turn == 'w' else (7 - i)
            coord = (col*SQ_SIZE, row* SQ_SIZE)
            self.screen.blit(image, coord)
    

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif self.pending_promotion is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_promotion_click(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.handle_mouse_up(event.pos)

    def run(self):
        while self.running:
            self.draw()
            for event in pygame.event.get():
                self.handle_event(event)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    board = Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R3KBNR w KQkq - 0 1")
    ChessGUI(board).run()



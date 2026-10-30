import pygame
import sys
from pathlib import Path
import numpy as np
from chess_engine.board import Board

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
        self.dragging_index = None
        self.legal_moves = []
        self.running = True


    def draw_board(self, scale: int):
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(col * scale, row * scale, scale, scale)
                pygame.draw.rect(self.screen, DARK if ((row + col) % 2) != INVERT else LIGHT, rect)
        if self.selected_square:
            col, row = self.selected_square
            rect = pygame.Rect(col * scale, row * scale, scale, scale)
            pygame.draw.rect(self.screen, list(i + 50 for i in DARK) if ((row + col) % 2) != INVERT else list(i - 40 for i in LIGHT) , rect)

    def draw_pieces(self):
        for pos, item in enumerate(self.board.board):
            if item is not None:
                key = SYMBOL_TO_PIECE[item]
                x,y = pos%8, 7 - pos//8
            else:
                continue
            if key in self.pieces and self.dragging_index != pos: # != (x, y):
                self.screen.blit(self.pieces[key], (x*SQ_SIZE, y*SQ_SIZE))

    def get_square(self):
        mouse_pos = pygame.mouse.get_pos()
        col = mouse_pos[0] // SQ_SIZE
        row = mouse_pos[1] // SQ_SIZE
        return (col, row)

    def draw_rect(self, square, color, width=3):
        col, row = square
        rect = pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        pygame.draw.rect(self.screen, color, rect, width)

    def get_moves_from_board(self, piece, pos):
        if piece == 'r':
            return self.board.get_piece_positions(self.board.generate_rook_moves(1<<pos, self.board.black_occupancy, self.board.white_occupancy))
        elif piece == 'R':
            return self.board.get_piece_positions(self.board.generate_rook_moves(1<<pos, self.board.white_occupancy, self.board.black_occupancy))
        elif piece == 'n':
            return self.board.get_piece_positions(self.board.generate_knight_moves(1<<pos, self.board.black_occupancy))
        elif piece == 'N':
            return self.board.get_piece_positions(self.board.generate_knight_moves(1<<pos, self.board.white_occupancy)) 
        elif piece == 'b':
            return self.board.get_piece_positions(self.board.generate_bishop_moves(1<<pos, self.board.black_occupancy, self.board.white_occupancy))
        elif piece == 'B':
            return self.board.get_piece_positions(self.board.generate_bishop_moves(1<<pos, self.board.white_occupancy, self.board.black_occupancy)) 
        elif piece == 'q':
            return self.board.get_piece_positions(self.board.generate_queen_moves(1<<pos, self.board.black_occupancy, self.board.white_occupancy))
        elif piece == 'Q':
            return self.board.get_piece_positions(self.board.generate_queen_moves(1<<pos, self.board.white_occupancy, self.board.black_occupancy)) 
        elif piece == 'k':
            return self.board.get_piece_positions(self.board.generate_king_moves(1<<pos, self.board.black_occupancy, self.board.white_occupancy))
        elif piece == 'K':
            return self.board.get_piece_positions(self.board.generate_king_moves(1<<pos, self.board.white_occupancy, self.board.black_occupancy)) 
        # elif piece == 'p':
        #             return self.board.generate_knight_moves(1<<pos, self.board.white_occupancy)
        # elif piece == 'P':
        #             return self.board.generate_knight_moves(1<<pos, self.board.black_occupancy) 
        
        

    def run(self):
        while self.running:
            self.draw_board(SQ_SIZE)
            self.draw_pieces()
            if self.selected_square:
                self.draw_rect(self.selected_square, (255, 0, 0), 4)
            if self.legal_moves:
                for pos in self.legal_moves:
                    y,x = 7 - (pos)//8, (pos)%8
                    pygame.draw.circle(self.screen, (80,90,100), (x*SQ_SIZE + SQ_SIZE //2, y*SQ_SIZE + SQ_SIZE//2), SQ_SIZE//8)
            if self.dragging and self.dragging_piece is not None:
                key = SYMBOL_TO_PIECE[self.dragging_piece]
                mouse_x, mouse_y = pygame.mouse.get_pos()
                image = self.pieces[key]
                w,h = image.get_width(), image.get_height()
                scaled_piece = pygame.transform.smoothscale(image, (int(w*1.1), int(h*1.1)))
                self.screen.blit(scaled_piece, (mouse_x - SQ_SIZE//2, mouse_y - SQ_SIZE//2))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    square = self.get_square()
                    index = (7 - square[1]) * 8 + square[0]

                    if not self.board.check_board_square(index):
                        self.selected_square = None
                        self.dragging = None 
                        self.dragging_piece = None 
                        self.dragging_index = None 
                        continue

                    piece = self.board.get_piece(index)

                    self.legal_moves = self.get_moves_from_board(piece, index)
                    self.selected_square = square
                    self.draw_rect(square, (255, 0, 0), 4)
                    self.dragging = True 
                    self.dragging_piece = piece
                    self.dragging_index = index 

                if event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = False
                    self.dragging_index = None
                    # self.dragging_piece = None
                    pygame.display.flip()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    board = Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    ChessGUI(board).run()




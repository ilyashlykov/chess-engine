import pygame
import sys
from pathlib import Path
import numpy as np
from chess_engine.board import Board

SQ_SIZE = 120
BOARD_SIZE = 8 * SQ_SIZE
ASSETS = Path(__file__).parent / ".." / "assets" / "pieces" / "alpha"
# ASSETS = Path(__file__).parent/ "assets" / "pieces" / "alpha"
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
            if key in self.pieces:
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

    def run(self):
        while self.running:
            self.draw_board(SQ_SIZE)
            self.draw_pieces()
            if self.selected_square:
                self.draw_rect(self.selected_square, (255, 0, 0), 4)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    square = self.get_square()
                    self.selected_square = square
                    print(f"Clicked on square: {square}")
                    self.draw_rect(square, (255, 0, 0), 4)

            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    board = Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    ChessGUI(board).run()




"""Simple (and slow) implementation of the game of life,
using numpy matrices for internal board representation,
and pillow to generate a gif visualization.
    pip install numpy Pillow
    python gol.py
Outputs: gol.gif
"""

import itertools
import numpy as np
from PIL import Image

SIZE = 100
DENSITY = 1/3
ALIVE, DEAD = 255, 0
BORN_STATES, SURVIVE_STATES = {3}, {2, 3}


def next_board(board):
    """Return a new matrix, the next state of given board"""
    return np.matrix([
        [ALIVE if isalive(board, row, col) else DEAD
         for col in range(board[row].size)]
        for row in range(board[2].size)
    ])

def isalive(board, row, col):
    """True if cell at given row,col position in board must be alive at next step"""
    nb_neighbors = sum(1 if val == ALIVE else 0 for val in neighbors(board, row, col))
    cell_state = board[row, col]
    if cell_state == ALIVE:
        return ALIVE if nb_neighbors in SURVIVE_STATES else DEAD
    elif cell_state == DEAD:
        return ALIVE if nb_neighbors in BORN_STATES else DEAD
    else:
        raise ValueError("Invalid cell state: " + str(cell_state))

def neighbors(board, row, col) -> tuple:
    """Return neighbors of given row,col position in board"""
    dimrow = board.size // len(board)
    dimcol = lambda row: board[row].size
    for drow, dcol in itertools.product((-1, 0, 1), repeat=2):
        if drow or dcol:  # discard the (0, 0) case
            x = (row + drow) % dimrow
            y = (col + dcol) % dimcol(x)
            yield board[x, y]


def image_of(board):
    """Build image from numpy array"""
    return Image.fromarray(board.astype('uint8'), mode='L')

def make_gif(files, target:str):
    """Build gif from given grayscales images"""
    first, *lasts = files
    first.save(target, save_all=True, append_images=lasts, duration=10)


def gol(board, steps:int=10):
    """Run the game of life on given board"""
    images = []
    for step in range(steps):
        board = next_board(board)
        images.append(image_of(board))
    make_gif(images, 'gol.gif')


board = np.matrix([  # simple example proving basic behavior
    [0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0],
]) * ALIVE
board = np.random.choice([ALIVE, DEAD], size=(SIZE, SIZE), p=[DENSITY, 1-DENSITY])
gol(board, 100)
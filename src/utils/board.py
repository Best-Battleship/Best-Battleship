import random

# Constants
BOARD_SIZE = 10
UNKNOWN, EMPTY, SHIP, HIT, MISS = '#', '.', 'S', 'X', 'O'
SHIP_SIZES = {'Carrier': 5, 'Battleship': 4, 'Cruiser': 3, 'Submarine': 3, 'Destroyer': 2}

def init_board():
    return [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]

def apply_shot(board, y, x):
    if board[y][x] == SHIP:
        board[y][x] = HIT
        return "HIT"
    elif board[y][x] == EMPTY:
        board[y][x] = MISS
        return "MISS"
    
def mark_shot(board, y, x, status):
    board[y][x] = status

    
def already_shot(board, y, x):
    return board[y][x] == HIT or board[y][x] == MISS


def all_ships_shot(board):
    return all(SHIP not in row for row in board)

def can_place_ship(board, ship_size, x, y, direction):
    if direction == 'H':
        return all(board[x][y+i] == EMPTY for i in range(ship_size) if y+i < BOARD_SIZE) and y+ship_size<BOARD_SIZE
    elif direction == 'V':
        return all(board[x+i][y] == EMPTY for i in range(ship_size) if x+i < BOARD_SIZE) and x+ship_size<BOARD_SIZE
    return False

def place_ship(board, ship_size, y, x, direction):
    if direction == 'H':
        for i in range(ship_size):
            board[y][x+i] = SHIP
    elif direction == 'V':
        for i in range(ship_size):
            board[y+i][x] = SHIP
            
def can_shoot(y, x):
    return (0 <= y < BOARD_SIZE and 0 <= x < BOARD_SIZE)

def already_shot(y, x, board):
    return board[y][x] != EMPTY

# Randomly place all ships
def place_all_ships(board):
    for _, size in SHIP_SIZES.items():
        placed = False
        while not placed:
            y, x = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
            direction = random.choice(['H', 'V'])
            if can_place_ship(board, size, y, x, direction):
                place_ship(board, size, y, x, direction)
                placed = True
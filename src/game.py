import random

  

# Constants
BOARD_SIZE = 10
SHIP_SIZES = {'Carrier': 5, 'Battleship': 4, 'Cruiser': 3, 'Submarine': 3, 'Destroyer': 2}
EMPTY, SHIP, HIT, MISS = '.', 'S', 'X', 'O'

  

# Initialize board

def init_board(size):
    return [[EMPTY]*size for _ in range(size)]

  

# Print board

def print_board(board):
    for row in board:
        print(' '.join(row))
    print()

  

# Check if placement is possible

def can_place_ship(board, ship_size, x, y, direction):
    if direction == 'H':
        return all(board[x][y+i] == EMPTY for i in range(ship_size) if y+i < BOARD_SIZE) and y+ship_size<BOARD_SIZE
    elif direction == 'V':
        return all(board[x+i][y] == EMPTY for i in range(ship_size) if x+i < BOARD_SIZE) and x+ship_size<BOARD_SIZE
    return False

  

# Place ship

def place_ship(board, ship_size, x, y, direction):
    if direction == 'H':
        for i in range(ship_size):
            board[x][y+i] = SHIP
    elif direction == 'V':
        for i in range(ship_size):
            board[x+i][y] = SHIP

  
  

# Randomly place all ships
def place_all_ships(board):
    for ship, size in SHIP_SIZES.items():
        placed = False
        while not placed:
            x, y = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
            direction = random.choice(['H', 'V'])
            if can_place_ship(board, size, x, y, direction):
                place_ship(board, size, x, y, direction)
                placed = True

  

# Take a shot
def take_shot(board, x, y):
    if board[x][y] == SHIP:
        board[x][y] = HIT
        print("Hit!")
    elif board[x][y] == EMPTY:
        board[x][y] = MISS
        print("Miss!")
    else:
        print("You already shot here.")

  

# Check for win

def check_win(board):
    return all(SHIP not in row for row in board)

  

# Main game loop

def play_game():

    player_board = init_board(BOARD_SIZE)
    enemy_board = init_board(BOARD_SIZE)

    place_all_ships(enemy_board)

    while True:
        print_board(enemy_board)
        x = int(input("Enter row: "))
        y = int(input("Enter column: "))

        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            print("Invalid coordinates.")
            continue

        take_shot(enemy_board, x, y)

        if check_win(enemy_board):
            print("You win!")
            break

  

play_game()
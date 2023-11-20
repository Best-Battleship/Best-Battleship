import random

from networking import *
import socket
import json
import random
import threading

# Global variables for netowrking part
MULTICAST_GRP = "224.1.1.1"  # Example multicast group
MULTICAST_PORT = 5007
GAME_PORT = 12345  # Game communication port
BUFFER_SIZE = 1024

# Global variables for game state
players = [(), ()]  # List of two tuples, each containing player ID and IP address
current_turn = 0  # Temporary turn management before token ring

# Constants
BOARD_SIZE = 10  # Defines the size of the game board (10x10).
SHIP_SIZES = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}  # Ship types and their sizes.
EMPTY, SHIP, HIT, MISS = (
    ".",
    "S",
    "X",
    "O",
)  # Symbols representing empty space, ship, hit, and miss.\


# Initialize board


def init_board(size):
    """
    Initialize the game board with a specified size.

    Args:
        size (int): The size of the board (number of rows and columns).

    Returns:
        list: A 2D list representing the game board initialized with empty spaces.
    """
    return [[EMPTY] * size for _ in range(size)]


# Print board


def print_board(board):
    """
    Print the game board in a readable format.

    Args:
        board (list): The game board to be printed.
    """
    for row in board:
        print(" ".join(row))
    print()


# Check if placement is possible


def can_place_ship(board, ship_size, x, y, direction):
    """
    Check if a ship can be placed at the specified location and direction.

    Args:
        board (list): The game board.
        ship_size (int): The size of the ship to be placed.
        x (int): The row number where the ship's placement begins.
        y (int): The column number where the ship's placement begins.
        direction (str): The direction of the ship ('H' for horizontal, 'V' for vertical).

    Returns:
        bool: True if the ship can be placed, False otherwise.
    """
    if direction == "H":
        return (
            all(
                board[x][y + i] == EMPTY for i in range(ship_size) if y + i < BOARD_SIZE
            )
            and y + ship_size < BOARD_SIZE
        )
    elif direction == "V":
        return (
            all(
                board[x + i][y] == EMPTY for i in range(ship_size) if x + i < BOARD_SIZE
            )
            and x + ship_size < BOARD_SIZE
        )
    return False


# Place ship


def place_ship(board, ship_size, x, y, direction):
    """
    Place a ship on the board at the specified location and direction.

    Args:
        board (list): The game board.
        ship_size (int): The size of the ship to be placed.
        x (int): The row number where the ship's placement begins.
        y (int): The column number where the ship's placement begins.
        direction (str): The direction of the ship ('H' for horizontal, 'V' for vertical).
    """
    if direction == "H":
        for i in range(ship_size):
            board[x][y + i] = SHIP
    elif direction == "V":
        for i in range(ship_size):
            board[x + i][y] = SHIP


# Randomly place all ships
def place_all_ships(board):
    """
    Randomly place all types of ships on the board.

    Args:
        board (list): The game board where the ships are to be placed.
    """
    for ship, size in SHIP_SIZES.items():
        placed = False
        while not placed:
            x, y = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
            direction = random.choice(["H", "V"])
            if can_place_ship(board, size, x, y, direction):
                place_ship(board, size, x, y, direction)
                placed = True


# Take a shot
def take_shot(board, x, y):
    """
    Take a shot at the specified coordinates on the board.

    Args:
        board (list): The game board.
        x (int): The row number to shoot at.
        y (int): The column number to shoot at.
    """
    if board[x][y] == SHIP:
        board[x][y] = HIT
        print("Hit!")
    elif board[x][y] == EMPTY:
        board[x][y] = MISS
        print("Miss!")
    else:
        print("You already shot here.")
    return board


# Check for win


def check_win(board):
    return all(SHIP not in row for row in board)


def play_game(initiator=False):
    global current_turn, players
    player_board = init_board(BOARD_SIZE)
    enemy_board = init_board(BOARD_SIZE)

    if initiator:
        # Initiator starts the game
        start_game_as_initiator(player_board)
        place_all_ships(player_board)
        current_turn = 0  # Initiator starts
        players.append("initiator_ip")  # Add initiator's IP

        # Broadcast initial board state to all players
        broadcast_board_state(player_board)

        # Main game loop for the initiator
        while True:
            if current_turn == 0:  # Initiator's turn
                print_board(enemy_board)
                x = int(input("Enter row: "))
                y = int(input("Enter column: "))

                if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                    print("Invalid coordinates.")
                    continue

                take_shot(enemy_board, x, y)
                if check_win(enemy_board):
                    print("You win!")
                    update_all_players()
                    break
                update_all_players()  # Update all players after the move
            else:
                # Wait for the turn to come back
                wait_for_turn()
    else:
        # Non-initiator player joins the game
        listen_for_multicast(handle_init_game_player)

        # Main game loop for non-initiator players
        while True:
            if is_my_turn():
                print_board(enemy_board)
                x = int(input("Enter row: "))
                y = int(input("Enter column: "))

                if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                    print("Invalid coordinates.")
                    continue

                take_shot(enemy_board, x, y)
                if check_win(enemy_board):
                    print("You win!")
                    update_all_players()
                    break
                update_all_players()  # Update all players after the move
                # make_move(player_board)
            else:
                wait_for_turn()


if __name__ == "__main__":
    # Start the UDP listener in a separate thread
    threading.Thread(target=udp_listener, args=(), daemon=True).start()
    user_choice = input("Do you want to start a game? y/n: ").lower()
    initiator_mode = user_choice == "y"
    play_game(initiator=initiator_mode)

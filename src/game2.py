import random

# Game Constants

BOARD_SIZE = 10
UNKNOWN, EMPTY, SHIP, HIT, MISS = '#', '.', 'S', 'X', 'O'
SHIP_SIZES = {'Carrier': 5, 'Battleship': 4, 'Cruiser': 3, 'Submarine': 3, 'Destroyer': 2}

# Networking constants
TIMEOUT = "timeout"
HOST = "0.0.0.0" # This should be server ip
PORT = 65432





# ------------------ BOARD OPERATIONS--------------------

def init_board():
    return [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]

def print_board(board):
    for row in board:
        print(' '.join(row))
    print()

def apply_shot(board, x, y):
    if board[x][y] == SHIP:
        board[x][y] = HIT
    elif board[x][y] == EMPTY:
        board[x][y] = MISS
    
def already_shot(board, x, y):
    return board[x][y] == HIT or board[x][y] == MISS


def all_ships_shot(board):
    return all(SHIP not in row for row in board)

def can_place_ship(board, ship_size, x, y, direction):
    if direction == 'H':
        return all(board[x][y+i] == EMPTY for i in range(ship_size) if y+i < BOARD_SIZE) and y+ship_size<BOARD_SIZE
    elif direction == 'V':
        return all(board[x+i][y] == EMPTY for i in range(ship_size) if x+i < BOARD_SIZE) and x+ship_size<BOARD_SIZE
    return False

def place_ship(board, ship_size, x, y, direction):
    if direction == 'H':
        for i in range(ship_size):
            board[x][y+i] = SHIP
    elif direction == 'V':
        for i in range(ship_size):
            board[x+i][y] = SHIP

# Randomly place all ships
def place_all_ships(board):
    for _, size in SHIP_SIZES.items():
        placed = False
        while not placed:
            x, y = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
            direction = random.choice(['H', 'V'])
            if can_place_ship(board, size, x, y, direction):
                place_ship(board, size, x, y, direction)
                placed = True
                
                
                

# -------------- GAME STATE -----------------------       

own_board = init_board()
self_index = -1
self_id = -1
players = []
player_boards = []
token = "asd123"
previous_move_x = -1
previous_move_y = -1





# ------------- UTILS -----------------
def get_next_player(self_index, player_ids):
    return players[(self_index + 1) % len(player_ids)]

def get_all_ips(players):
    return [player["ip"] for player in players]

def add_player(ip):
    # TODO: Error handling for IP already being present
    players.append({"ip": ip, "id": random.randint()})
    return players[-1].id







# ----------- NETWORKING DUMMIES ----------------
## Should messages be JSON payloads?

def broadcast(message):
    # Broadcast given message
    pass

def send_to_many(ips, message):
    # Do concurrent sends with token
    # Collect all responses
    # Return responses
    # Timeout should have a special response to indicate to the caller
    pass

def send_to_one(ip, message):
    # Send with token
    # Return response
    # Timeout should have a special response, e.g. TIMEOUT
    pass








# -------------- PROTOCOLS ----------------------

# Protocol 0: IDLE

def IDLE():
    # Wait for any message
    # Handle incoming messages as per protocols

    ## E.g. 
    # message = {"message": "INIT_GAME"}
    ## ip = get_ip_from_message
    ## JOIN_GAME(ip)
    
    # Could also have timeouts for certain waits or context-aware waits, such as WAITING_FOR_GAME_START
    pass





# Protocol 1: START
## INITIALIZER: INIT_GAME -> WAIT_FOR_JOINS -> START_GAME -> play_own_turn
## PLAYER: (RECEIVES INIT_GAME) -> JOIN_GAME -> WAIT_FOR_START


# INITIALIZER:
def START_GAME():    
    acks = send_to_many(get_all_ips(players), {"message": "START_GAME", "players": players})

    # Someone says no
    if any(x == "NAK" for x in acks):
        # What to do?
        pass
    # All say yes
    elif all(x == acks[0] for x in acks):
        # Time to play own turn
        play_own_turn()
    else:
        # Timeout handling
        ## Move to dropping a node / election
        pass

def WAIT_FOR_JOINS():
    # Listen on own socket
    # When receiving {"message": "JOIN_GAME"}
    ## get ip from message
    ## id = add_player(ip)
    ## send_to_one(ip, {"message": "ACK_JOIN_GAME", "id": id})
    # After constant time stop waiting
    return START_GAME()

def INIT_GAME():
    add_player(HOST)
    broadcast({"message": "INIT_GAME", "ip": HOST}) # IP may be redundant here
    return WAIT_FOR_JOINS()



# PLAYER:
def WAIT_FOR_START():
    # Listen on own socket
    # When receiving {"message": "START_GAME", "players": players} from ip
    ## send_to_one(ip, {"message": "ACK_START_GAME"})
    ## Generate empty boards for all other players
    ## return IDLE
    # After constant time timeout
    pass
    
def JOIN_GAME(ip):
    own_board = place_all_ships(own_board)
    
    # Tell the initializer you want to join the game
    ack = send_to_one(ip, {"message": "JOIN_GAME"})
    
    if ack == TIMEOUT:
        own_board = init_board()
        return IDLE()
    elif ack["message"] == "ACK_JOIN_GAME":
        self_id = ack["message"]["id"]
        return WAIT_FOR_START()
    else:
        # NAK, what to do? Reset and wait for new game?
        own_board = init_board()
        return IDLE()
    
    
    
    
    
    
# Protocol 2: PLAY_TURN
## CURRENT PLAYER: (play_own_turn) -> PLAY_TURN -> PASS_TOKEN -> (IDLE OR WIN)
## NEXT PLAYER: (receives PLAY_TURN) -> WAIT_FOR_PASS_TOKEN -> MOVE_RESULT -> (PLAY_TURN OR LOSE)
## OTHERS: (receives PLAY_TURN) -> WAIT_FOR_PASS_TOKEN -> WAIT_FOR_MOVE_RESULT -> IDLE
      
# CURRENT PLAYER:

def PLAY_TURN(next_player, x, y):
    # Get next player id
    next_player_id = next_player["id"]

    # Send to all others
    acks = send_to_many(get_all_ips(), {"message": "PLAY_TURN", "target": next_player_id, "x": x, "y": y})

    # Someone says no
    if any(x == "NAK" for x in acks):
        # What to do?
        pass
    # All say yes
    elif all(x == acks[0] for x in acks):
        # Store move for checking later
        previous_move_x = x
        previous_move_y = y
        return PASS_TOKEN(next_player)
    else:
        # Timeout handling
        ## Move to dropping a node / election
        pass
    
def PASS_TOKEN(next_player):
    # Send to all others
    acks = send_to_many(get_all_ips(), {"message": "PASS_TOKEN", "id": next_player["id"]})

    # Someone says no
    if any(x == "NAK" for x in acks):
        # What to do?
        pass
    # All say yes
    elif all(x == acks[0] for x in acks):
        # Tell the next player that passing the token is ACKd
        ack = send_to_one(next_player["ip"], {"message": "PASS_TOKEN_CONFIRMED"})
        
        if ack:
            return IDLE()
        elif "timeout":
            # Timeout handling
            pass
        else:
            # NAK, what to do?
            pass
    else:
        # Timeout handling
        ## Move to dropping a node / election
        pass

# NEXT PLAYER:
def MOVE_RESULT():
    # Apply shot to own board
    apply_shot(own_board[previous_move_x][previous_move_y])
    # Send to all others
    acks = send_to_many(get_all_ips(),{"message":  "MOVE_RESULT", "result": own_board[previous_move_x][previous_move_y]})

    # Someone says no
    if any(x == "NAK" for x in acks):
        # What to do?
        pass
    # All say yes
    elif all(x == acks[0] for x in acks):
        # Time to play own turn
        return play_own_turn()
    else:
        # Timeout handling
        ## Move to dropping a node / election
        pass

def LOST():
    # Send to all others
    acks = send_to_many(get_all_ips(), {"message": "LOST", "id": self_id})

    # Someone says no
    if any(x == "NAK" for x in acks):
        # What to do?
        pass
    # All say yes
    elif all(x == acks[0] for x in acks):
        # Maybe keep listening to the game?
        return
    else:
        # Timeout handling
        ## Move to dropping a node / election
        pass
    
def WAIT_FOR_ACK_PASS_TOKEN():
    # listen on own socket
    # when message = {"message": "PASS_TOKEN_CONFIRMED"}
    ## return MOVE_RESULT()
    # timeouts after constant time
    pass

# OTHERS:

def WAIT_FOR_MOVE_RESULT():
    # listen on own socket
    # when message = {"message": "MOVE_RESULT"}
    ## commit the move
    ## apply_shot(current_player_board, x, y)
    ## ack
    ## return IDLE()
    # timeouts after constant time
    pass

def WAIT_FOR_PASS_TOKEN():
    # Validate, assume ok for now
    # send_to_one(message.ip, {"message": "ACK_PASS_TOKEN"})
    # When token receiver
    ## return WAIT_FOR_ACK_PASS_TOKEN
    # return WAIT_FOR_MOVE_RESULT
    # timeouts after constant time
    pass

def RECV_PLAY_TURN(ip, message):
    # Validate, assume ok for now
    # send_to_one(message.ip, {"message": "ACK_PLAY_TURN"})
    previous_move_x = message.x
    previous_move_y = message.y
    # return WAIT_FOR_PASS_TOKEN()
    
    


# Protocol 7: PLAYER LOST OR SURRENDERED
# ....    
    


# Game loop for the player

def play_own_turn():
    # Check own status
    if all_ships_shot(player_boards[self_index]):
        LOST()
    else:
        # Get next player and their board
        next_player = get_next_player(self_index, players)
        enemy_board = next_player["board"]

        # May have to try a couple of times to hit the board or unshot space
        while True:
            print_board(enemy_board)
            x = int(input("Enter row: "))
            y = int(input("Enter column: "))

            # Can't shoot off the board
            if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                print("Invalid coordinates.")
                continue

            # Optional: allow trying again if shooting an already shot space
            if enemy_board[x][y] != UNKNOWN:
                print("You already shot here.")
                continue

            # Commit to the shot
            PLAY_TURN(next_player, x, y)
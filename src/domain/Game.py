from utils.board import *

class Game:
    # The player's own index
    own_index = -1
    own_board = None
    def __init__(self, ui, messaging_service):
        self.ui = ui
        self.messaging_service = messaging_service
        self.players = []
        
    def create_game(self):
        # Initialize a new game
        print("TODO: Initialize a new game")
        # CREATE_GAME
        
    def wait_for_a_game(self):
        # Start waiting for a game
        print("TODO: Initialize a new game")
        
    def generate_own_board(self):
        own_board = init_board(self.EMPTY, self.BOARD_SIZE)
        
    def generate_board_for_player(self, player):
        print("TODO: initialize a board for the player")
        # player["board"] = init_board(self.EMPTY, self.BOARD_SIZE)
        
    def add_player(self, player):
        print("TODO: Add the player tuple (ID, IP, PORT, BOARD) to players")
        # self.players.append(player)
        
    def remove_player(self, player):
        print("TODO: removing a player")
        # flag or array ops?
        
    def get_next_player(self):
        # TODO: Add handling for removed players if using flag.
        return self.players[(self.own_index + 1) % len(self.players)]
        
    def play_turn(self):
        # Check own status
        if all_ships_shot(self.own_board):
            print("TODO: start LOST protocol")
            pass
        else:
            # Get next player and their board
            next_player = self.get_next_player()
            enemy_board = next_player["board"]

            # May have to try a couple of times to hit the board or unshot space
            while True:
                self.ui.render_board(enemy_board)
                y = self.ui.request_numeric_input("Enter row: ")
                x = self.ui.request_numeric_input("Enter column: ")

                # Can't shoot off the board
                if not can_shoot(y, x):
                    self.ui.display_message("Invalid coordinates.")
                    continue

                # Optional: allow trying again if shooting an already shot space
                if already_shot(y, x, enemy_board):
                    self.ui.display_message("You already shot here.")
                    continue

                # Commit to the shot
                print("TODO: Move to PLAY_TURN protocol")
                # PLAY_TURN(next_player, x, y)
    
    
    
    
    # -------------------- PROTOCOLS -----------------------
    
    # Protocol 0: IDLE

    def IDLE(self):
        # Wait for any message
        # Handle incoming messages as per protocols

        ## E.g. 
        # message = {"message": "INIT_GAME", "ip": <ip>, "port": <port>}
        ## JOIN_GAME(message["ip"])
        
        # Could also have timeouts for certain waits or context-aware waits, such as WAITING_FOR_GAME_START
        pass
        
    # Protocol 1: START
    ## INITIALIZER: INIT_GAME -> WAIT_FOR_JOINS -> START_GAME -> play_own_turn
    ## PLAYER: (RECEIVES INIT_GAME) -> JOIN_GAME -> WAIT_FOR_START


    # INITIALIZER:
    def CREATE_GAME(self): 
        return
        #self.messaging_service.send_to_network({"INIT_GAME"})
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

    def INIT_GAME(self):
        self.add_player()
        broadcast({"message": "INIT_GAME", "ip": HOST}) # IP may be redundant here
        return WAIT_FOR_JOINS()



    # PLAYER:
    def WAIT_FOR_START(self):
        # Listen on own socket
        # When receiving {"message": "START_GAME", "players": players} from ip
        ## send_to_one(ip, {"message": "ACK_START_GAME"})
        ## Generate empty boards for all other players
        ## return IDLE
        # After constant time timeout
        pass
        
    def JOIN_GAME(self):
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

    def PLAY_TURN(self, next_player, x, y):
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
        
    def PASS_TOKEN(self, next_player):
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
    def MOVE_RESULT(self):
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

    def LOST(self):
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
        
    def WAIT_FOR_ACK_PASS_TOKEN(self):
        # listen on own socket
        # when message = {"message": "PASS_TOKEN_CONFIRMED"}
        ## return MOVE_RESULT()
        # timeouts after constant time
        pass

    # OTHERS:

    def WAIT_FOR_MOVE_RESULT(self):
        # listen on own socket
        # when message = {"message": "MOVE_RESULT"}
        ## commit the move
        ## apply_shot(current_player_board, x, y)
        ## ack
        ## return IDLE()
        # timeouts after constant time
        pass

    def WAIT_FOR_PASS_TOKEN(self):
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
    
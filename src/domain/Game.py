import time
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
        self.ui.display_message("Starting a new game!")
        self.INIT_GAME()
        
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
                
                
    # ---------------- PROTOCOLS --------------------
    
    # INIT GAME
    def INIT_GAME(self):
        self.ui.display_message("Sending INIT_GAME")
        self.messaging_service.broadcast({"message": "INIT_GAME"})
        # Make a function out of this maybe
        five_sec_timer = time.time() + 5
        while time.time() < five_sec_timer:
            message = self.messaging_service.listen_broadcast()
            print(message)
            if message["message"] == "JOIN_GAME":
                player = message
                self.messaging_service.send_to(player, {"message": "ACK_JOIN"})
                self.players.append(player)
                self.ui.display_message("Added a player!")
            else:
                # Implement handling for non-happy paths
                pass
            
        # Add self to game
        self.players.append({"ip": self.messaging_service.messaging_client.IP, "port": self.messaging_service.messaging_client.IP, "broadcast_port": self.messaging_service.messaging_client.PORTB})

        self.messaging_service.send_to_many({"message": "START_GAME", "players": self.players})
        
        # Make a function out of this maybe
        five_sec_timer = time.time() + 5
        ackd_players = 0
        while time.time() < five_sec_timer and ackd_players < len(self.players) - 1:
            message = self.messaging_service.listen_broadcast()
            if message["message"] == "ACK_START_GAME":
                ackd_players += 1
            else:
                # Implement handling for non-happy paths
                # Maybe ignore other messages at this point?
                pass
        
        if ackd_players < len(self.players) - 1:
            self.ui.display_message("Failed to start a game!")
            return
            
        self.ui.display_message("game started by you...")
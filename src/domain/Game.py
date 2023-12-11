import time

from utils.board import *
from models.NetworkResult import Status


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
        self.ui.display_message("Waiting for a new game!")
        self.JOIN_GAME()

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

    def remove_self_from_game(self):
        # Remove self from the players list
        self.players = [
            player
            for player in self.players
            if player["ip"] != self.messaging_service.messaging_client.IP
        ]
        self.ui.display_message("Removed self from players list.")

    def get_next_player(self):
        # TODO: Add handling for removed players if using flag.
        return self.players[(self.own_index + 1) % len(self.players)]

    def play_turn(self):
        # Check own status
        if all_ships_shot(self.own_board):
            print("TODO: start LOST protocol")
            self.LOST_GAME()
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
            result = self.messaging_service.listen_broadcast()
            if result.status == Status.OK and result.message["message"] == "JOIN_GAME":
                player = {
                    "ip": result.ip,
                    "port": result.port,
                    "broadcast_port": int(result.message["broadcast_port"]),
                }
                self.messaging_service.send_to(
                    (result.ip, result.port), {"message": "ACK_JOIN"}
                )
                self.players.append(player)
                self.ui.display_message("Added a player!")
            else:
                # Implement handling for non-happy paths
                print("Not OK", result.status.name)
                pass

        if len(self.players) == 0:
            self.ui.display_message("No one here...")
            return

        # Add self to game
        self.players.append(
            {
                "ip": self.messaging_service.messaging_client.IP,
                "port": self.messaging_service.messaging_client.PORT,
                "broadcast_port": self.messaging_service.messaging_client.PORTB,
            }
        )

        self.ui.display_message("Multicasting START_GAME")
        self.messaging_service.send_to_many(
            {"message": "START_GAME", "players": self.players}
        )

        # Make a function out of this maybe
        five_sec_timer = time.time() + 5
        ackd_players = []
        while (
            time.time() < five_sec_timer and len(ackd_players) < len(self.players) - 1
        ):
            result = self.messaging_service.listen_broadcast()
            if (
                result.status == Status.OK
                and result.message["message"] == "ACK_START_GAME"
            ):
                ackd_players.extend(
                    filter(lambda p: p["ip"] == result.ip, self.players)
                )
            else:
                # Implement handling for non-happy paths
                # Maybe ignore other messages at this point?
                print("Not OK", result.status.name)
                pass

        if len(ackd_players) < len(self.players) - 1:
            self.ui.display_message("Failed to start a game!")
            return

        self.ui.display_message("game started by you...")

    # JOIN GAME
    def JOIN_GAME(self):
        self.ui.display_message("Waiting for INIT_GAME broadcast...")
        result = self.messaging_service.listen_broadcast(None)

        if result.status == Status.OK and result.message["message"] == "INIT_GAME":
            initiator = (result.ip, result.port)
            self.messaging_service.send_to(
                initiator,
                {
                    "message": "JOIN_GAME",
                    "broadcast_port": self.messaging_service.messaging_client.PORTB,
                },
            )

            result = self.messaging_service.listen()

            if result.status == Status.OK and result.message["message"] == "ACK_JOIN":
                self.ui.display_message(
                    "Joined the game! Waiting for START_GAME multicast..."
                )
                result = self.messaging_service.listen_multicast(
                    6
                )  # should start in 5 sec

                # TODO code
                if result.status == Status.OK:
                    (ip, port) = initiator
                    self.messaging_service.send_to(
                        (result.ip, port), {"message": "ACK_START_GAME"}
                    )
                else:
                    # Implement handling for non-happy paths
                    print("Not OK", result.status.name)
                    pass
            else:
                # Implement handling for non-happy paths
                print("Not OK", result.status.name)
                pass
        else:
            # Implement handling for non-happy paths
            print("Not OK", result.status.name)
            pass

    def LOST_GAME(self):
        # Broadcast 'LOST' message
        self.ui.display_message("Broadcasting 'LOST' message...")
        self.messaging_service.broadcast({"message": "LOST"})

        # Start timeout timer
        end_time = time.time() + 5  # 5-second timeout
        ack_players = []

        while time.time() < end_time:
            result = self.messaging_service.listen_broadcast()
            if result.status == Status.OK and result.message["message"] == "ACK_LOST":
                # Check if the player is in the game and hasn't already acknowledged
                if result.ip not in ack_players and any(
                    p["ip"] == result.ip for p in self.players
                ):
                    ack_players.append(result.ip)
                    self.ui.display_message(
                        f"Received 'ACK_LOST' from player {result.ip}"
                    )
            else:
                # Implement handling for non-happy paths, similarly?
                print("Not OK", result.status.name)
                pass

        # Check if all players have acknowledged
        if len(ack_players) == len(self.players) - 1:  # Exclude self
            self.ui.display_message("All players acknowledged the lost game.")
            self.remove_self_from_game()
        else:
            self.ui.display_message(
                "Failed to receive acknowledgment from all players."
            )
            pass

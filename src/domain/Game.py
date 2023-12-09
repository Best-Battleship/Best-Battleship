import time
import json

from utils.board import *
from models.NetworkResult import Status
from models.Player import Player

class Game:
    # The player's own index
    own_index = -1

    def __init__(self, ui, messaging_service):
        self.ui = ui
        self.messaging_service = messaging_service
        self.players = []
        self.own_id = 0
        self.own_board = None
        self.enemy_boards = {}
        self.token_keeper = None
        self.myself = None

    def create_game(self):
        self.ui.display_message("Starting a new game!")
        self.INIT_GAME()
        
    def wait_for_a_game(self):
        # Start waiting for a game
        self.ui.display_message("Waiting for a new game!")
        self.JOIN_GAME()
        
    def generate_own_board(self):
        self.own_board = init_board()
        place_all_ships(self.own_board)
        
    def generate_board_for_players(self):
        for player in self.players:
            if player.toJSON()["id"] != self.own_id:
                self.enemy_boards[player.toJSON()["id"]] = init_board()

    def check_and_mark_hits(self, enemy_shot):
        if enemy_shot.message["target_id"] == self.own_id:
            apply_shot(self.own_board, enemy_shot.message["y"],enemy_shot.message["x"])
        else:
            apply_shot(self.enemy_boards[enemy_shot.message["target_id"]], enemy_shot.message["y"],enemy_shot.message["x"])

    def map_player_from_json(self, json):
        try:                 
            number = json['id']
            ip = json['ip']
            port = int(json['broadcast_port'])
            return Player(number, ip, port)
        except: return None

    def add_player(self, player):
        print("TODO: Add the player tuple (ID, IP, PORT, BOARD) to players")
        # self.players.append(player)
    
    def set_host_as_token_holder(self):
        for player in self.players:
            if player.toJSON()["id"] == 0:
                self.token_keeper = player

    def drop_nodes(self, to_drop, players):
        active_players = [p for p in players if p not in to_drop]
        droped_players = []
        
        if len(active_players) == 0:
            print("Seems like you are the only one survived")
            self.players = []
            return
        
        for p in to_drop:
            if self.HANDLE_TIMEOUT_DROP_NODE(p, active_players):
                droped_players.append(p)
        
        return droped_players
        
    def get_next_player(self):
        # TODO: Add handling for removed players if using flag.
        print(str(self.own_id + 1))
        print(len(self.players))
        print((self.own_id + 1) % len(self.players))
        # return self.players[(self.own_id + 1) % len(self.players)]
        return self.get_player_with_player_id((self.own_id + 1) % len(self.players))
    
    
    def filter_players_by_id(self, removable_id):
        return [player for player in self.players if player.number != removable_id]
    
    def get_player_with_player_id(self, id):
        return next((player for player in self.players if player.number == id), None)

    def start_game(self):
        self.generate_own_board();
        self.generate_board_for_players();

        # Initiator or host will start the game
        if self.own_id != 0:
            self.wait_for_turn()

        self.ui.display_message("Multicasting START_GAME")
        json_players = [p.toJSON() for p in self.players]
        command = {"message": "START_GAME", "players": json_players}
        
        if self.command_loop(command, "ACK_START_GAME", self.players):
            self.ui.display_message("game started by you...")
            self.play_turn()
            return True
        else:
            self.ui.display_message("failed to start a game...")
            return False
        
    def wait_for_turn(self):
        self.ui.display_message("Waitin my turn to play...")
        enemy_shooting_result = self.listen_loop(self.token_keeper, "PLAY_TURN")
        # Who gets the token next
        token_result = self.listen_loop(self.token_keeper, "PASS_TOKEN")
        # Set the new token owner. Is this the right place?
        self.token_keeper = self.get_player_with_player_id(token_result.message["id"])
        if token_result.message["id"] == self.own_id:
            result = self.messaging_service.listen(10)
            print("result is "+str(result.message))
            if result.message["message"] == "PASS_TOKEN_CONFIRMED":
                self.token_keeper = self.myself
                #mark results
                shot_result = self.check_and_mark_hits(enemy_shooting_result)
                # prepare command
                shot_result = {"id": self.own_id, "message": "MOVE_RESULT", "result": shot_result}
                self.command_loop(shot_result, "MOVE_RESULT", self.players)

            else:
                # Did not get the confirmations
                pass
        elif token_result.message["id"] != self.own_id:
            shot_result = self.listen_loop(self.token_keeper, "MOVE_RESULT")
            if shot_result.message["result"] == "HIT":
                mark_shot(self.enemy_boards[enemy_shooting_result.message["target_id"]],enemy_shooting_result.message["y"],enemy_shooting_result.message["x"], HIT)
            elif shot_result.message["result"] == "MISS":
                mark_shot(self.enemy_boards[enemy_shooting_result.message["target_id"]],enemy_shooting_result.message["y"],enemy_shooting_result.message["x"], MISS)
        if self.token_keeper.number == self.own_id:
            # take the next turn
            self.play_turn()
        else:
            self.wait_for_turn()

        
    def play_turn(self):
        # Check own status
        if all_ships_shot(self.own_board):
            print("TODO: start LOST protocol")
            pass
        else:
            # Get next player and their board
            next_player = self.get_next_player()
            print("Next player is " + str(next_player.number))
            enemy_board = self.enemy_boards[next_player.toJSON()["id"]]

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
                self.PLAY_TURN(next_player, x, y)
                self.wait_for_turn()
        
                
    def listen_loop(self, token_keeper, message_to_listen):
        result = self.messaging_service.listen_multicast(6)
        
        if result.ip == token_keeper.ip:
            if result.status == Status.OK:
                if 'message' in result.message:
                    if result.message['message'] == message_to_listen:
                        for p in self.players:
                            if p.ip == result.ip:
                                message = result.message
                                
                                if 'token' in message:
                                    del message['token']
                                self.messaging_service.send_to((p.ip, p.port), message)
                                return result
                                
                    elif result.message['message'] == 'TIMEOUT':
                        self.HANDLE_RECEIVED_TIMEOUT(result)
                        return self.listen_loop(token_keeper, message_to_listen)
                        
                    elif result.message['message'] == 'ELECTION':
                        self.HANDLE_RECEIVED_ELECTION(result)
                        return self.listen_loop(token_keeper, message_to_listen)
                        
                    else:
                        print("unhandled result:", result.message['message'])
                        return False
                        
                else:
                    print("received result without a message")
                    return False
                    
            elif result.status == Status.UNHANDELED_TIMEOUT:
                self.HANDLE_TIMEOUT_TOKEN_LOST(token_keeper, result)
                return self.listen_loop(token_keeper, message_to_listen)
                
            else:
                print("got unhandled error status in listen loop")
                return False
                
        else:
            print("received multicast from wrong ip:", result.ip)
            return self.listen_loop(token_keeper, message_to_listen)
        
    def command_loop(self, command, ack_message, receivers, repeated_times = 0):

        if len(receivers) == 0:
            return True # everybody is dropped in receivers list
            
        if repeated_times > 3:
            return False # somebody is NAK:ing on everything, TODO: force drop
        
        if 'message' not in command:
            print("There should be a message in command:", command)
            return False
            
        if repeated_times > 0:
            command['repeated'] = 1 # works or not?
        
        self.messaging_service.send_to_many(command)
        not_acked = self.messaging_service.collect_acks(receivers, self.myself, ack_message)
        
        if len(not_acked) == 0:
            return True
        else:
            droped_players = self.drop_nodes(not_acked, receivers)
            receivers = [r for r in receivers if r not in droped_players]
            return self.command_loop(command, ack_message, receivers, repeated_times + 1)
    
    # ---------------- PROTOCOLS --------------------
    
    # INIT GAME
    def INIT_GAME(self):
        next_id = 1
    
        self.ui.display_message("Broadcasting INIT_GAME")
        self.messaging_service.broadcast({"message": "INIT_GAME"})
        
        # Not a command_loop because of unique logic
        five_sec_timer = time.time() + 5
        
        while time.time() < five_sec_timer:
            result = self.messaging_service.listen_broadcast()
            
            if result.status == Status.OK and result.message["message"] == "JOIN_GAME":
                player = Player(next_id, result.ip, int(result.message['broadcast_port']))
                self.messaging_service.send_to((result.ip, result.port), {"message": "ACK_JOIN"})
                self.players.append(player)
                next_id = next_id + 1
                
                self.ui.display_message("Added a player!")
            else:
                # Implement handling for non-happy paths
                print("Game initialisation ended. Start game.")
                pass
                
        # Add yourself to game
        self.myself = Player(0, 
            self.messaging_service.messaging_client.IP, 
            self.messaging_service.messaging_client.PORTB)
        self.players.append(self.myself)
        self.set_host_as_token_holder()

        if len(self.players) == 1:
            self.ui.display_message("No one here...")
            return
        
        self.start_game()
        
    # JOIN GAME
    def JOIN_GAME(self):
        self.ui.display_message("Waiting for INIT_GAME broadcast...")
        
        # not a listen_loop because of unique logic
        result = self.messaging_service.listen_broadcast(None)
        
        if result.status == Status.OK and result.message['message'] == "INIT_GAME":
            initiator = (result.ip, result.port)
            self.messaging_service.send_to(
                initiator, 
                {"message": "JOIN_GAME", "broadcast_port": self.messaging_service.messaging_client.PORTB})
                
            # not a listen_loop because of unique logic
            result = self.messaging_service.listen()
            
            if result.status == Status.OK and result.message['message'] == "ACK_JOIN":
                self.ui.display_message("Joined the game! Waiting for START_GAME multicast...")
                
                # not a listen_loop because no players list yet
                result = self.messaging_service.listen_multicast(6) # should start in 5 sec
                
                if result.status == Status.OK and result.message['message'] == "START_GAME":
                    (ip, port) = initiator
                    self.players = [self.map_player_from_json(player) for player in result.message['players'] if self.map_player_from_json(player) != None]
                    myself = [p for p in self.players if p.ip == self.messaging_service.messaging_client.IP]
                    self.set_host_as_token_holder()
                    self.own_id = myself[0].toJSON()["id"]
                    if len(myself) == 1:
                        self.myself = myself[0]
                        self.messaging_service.send_to(
                            (result.ip, port), 
                            {"message": "ACK_START_GAME"})
                    else:
                        print("You are not in player list!")
                    
                elif result.status == Status.OK and result.message['message'] == "TIOMEOUT":
                    HANDLE_RECEIVED_TIMEOUT(result) # missed START_GAME
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

    # PLAY TURN 
    def PLAY_TURN(self,next_player, x, y):
        self.ui.display_message("Sending for shot coordinates via multicast...")
        shot_command = {"target_id": next_player.toJSON()["id"], "message": "PLAY_TURN", "x": x, "y": y}
        token_command = {"message": "PASS_TOKEN", "id": next_player.toJSON()["id"]}

        # Inform shots
        if self.command_loop(shot_command, "PLAY_TURN", self.players):
            self.ui.display_message("Sending info or next token holder via multicast...")
            result = self.command_loop(token_command, "PASS_TOKEN", self.players)
            if result:
                print(str(next_player.ip)+" " + str(next_player.port))
                self.messaging_service.send_to((next_player.ip, 5005), {"message": "PASS_TOKEN_CONFIRMED"})
                self.token_keeper = next_player
                shot_result = self.listen_loop(self.token_keeper, "MOVE_RESULT")
                if shot_result.message["result"] == "HIT":
                    mark_shot(self.enemy_boards[next_player.number], y, x, HIT)
                elif shot_result.message["result"] == "MISS":
                    mark_shot(self.enemy_boards[next_player.number], y, x, MISS)

            else:
                # errors
                print("Did not get enough acks for PASS_TOKEN!")
                pass
        else:
            # Errors
            print("Did not get enough acks for PLAY_TURN!")
        return True


    def HANDLE_TIMEOUT_DROP_NODE(self, player, active_players):
        print("Sending TIMEOUT", player.ip)
        
        if len(active_players) < 2: # only you are active
            self.players = [self.myself]
            return True
            
        # not a command_loop because of NAK handling
        self.messaging_service.send_to_many({"message": "TIMEOUT", "ip": player.ip})
        
        five_sec_timer = time.time() + 5
        ackd_players = []
        
        while time.time() < five_sec_timer and len(ackd_players) < len(active_players) - 1:
            time_left = five_sec_timer - time.time()
            result = self.messaging_service.listen_broadcast(time_left)
            
            if result.status == Status.OK and result.message["message"] == "TIMEOUT":
                ackd_players.extend(filter(lambda p: p.ip == result.ip, active_players))
            elif result.status == Status.OK and result.message["message"] == "NAK" and result.ip == player.ip:
                return False
            else:
                pass
                
        if len(ackd_players) == len(active_players) - 1:
            command = {"message": "DROP", "ip": player.ip}
            
            if self.command_loop(command, "DROP", ackd_players):
                self.players = [p for p in self.players if p != player]
                return True
            else:
                # Implement handling for non-happy paths
                print("Not everybody ACKed on DROP")
                pass
        else:
            # Implement handling for non-happy paths
            print("Not everybody ACKed on TIMEOUT")
            pass
            
        return False
     
    def HANDLE_RECEIVED_TIMEOUT(self, result):
        
        self.ui.display_message("Received TIMEOUT")
        
        if result.message['ip'] == self.messaging_service.messaging_client.IP:
            message = {"message": "NAK"}
        else:
            message = {"message": "TIMEOUT", "ip": result.message['ip']}
                        
        for p in self.players:
            if p.ip == result.ip:
                token_keeper = p
                break
        
        self.messaging_service.send_to((token_keeper.ip, token_keeper.port), message)
        result = self.listen_loop(token_keeper, "DROP")
        
        if result.status == Status.OK and result.message['message'] == "DROP":
            self.players = [p for p in self.players if p.ip != result.message['ip']]
        
        self.ui.display_message("TIMEOUT handled")
        # continue the game
        
    def HANDLE_TIMEOUT_TOKEN_LOST(self, token_keeper):
        self.ui.display_message("Sending ELECTION")
        
        # not a command_loop because of NAK handling
        self.messaging_service.send_to_many({"message": "ELECTION"})
        
        five_sec_timer = time.time() + 5
        ackd_players = []
        
        while time.time() < five_sec_timer and len(ackd_players) < len(self.players) - 2:
            time_left = five_sec_timer - time.time()
            result = self.messaging_service.listen_broadcast(time_left)
            
            if result.status == Status.OK and result.message["message"] == "ELECTION":
                ackd_players.extend(filter(lambda p: p.ip == result.ip, active_players))
            elif result.status == Status.OK and result.message["message"] == "NAK" and result.ip == token_keeper.ip:
                return False
            else:
                pass
                
        if len(ackd_players) == len(self.players) - 2:
            command = {"message": "DROP", "ip": token_keeper.ip}
            
            if self.command_loop(command, "DROP", ackd_players):
                self.players = [p for p in self.players if p != token_keeper]
                
                # TODO: pass token to the next
                return True
            else:
                # Implement handling for non-happy paths
                print("Not everybody ACKed on DROP")
                pass
        else:
            # Implement handling for non-happy paths
            print("Not everybody ACKed on ELECTION")
            pass
            
        return False
        
    def HANDLE_RECEIVED_ELECTION(self, token_keeper, result):
        
        self.ui.display_message("Received ELECTION")
        
        if token_keeper.ip == self.messaging_service.messaging_client.IP:
            message = {"message": "NAK"}
        else:
            message = {"message": "ACK_ELECTION"}
                        
        for p in self.players:
            if p.ip == result.ip:
                token_keeper = p
                break
                    
        self.messaging_service.send_to((token_keeper.ip, token_keeper.port), message)
        result = self.listen_loop(token_keeper, "DROP")
        
        if result.status == Status.OK and result.message['message'] == "DROP":
            self.players = [p for p in self.players if p.ip != result.message['ip']]
        
        # TODO: change token owner
        self.ui.display_message("ELECTION handled")
        # continue the game
import time
import json
import threading

from utils.board import *
from models.NetworkResult import Status
from models.Player import Player

class Game:
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
            if player.number != self.own_id:
                self.enemy_boards[player.number] = init_board()

    def check_and_mark_hits(self, enemy_shot):
        if enemy_shot.message["target_id"] == self.own_id:
            return apply_shot(self.own_board, enemy_shot.message["y"],enemy_shot.message["x"])
        else:
            return apply_shot(self.enemy_boards[enemy_shot.message["target_id"]], enemy_shot.message["y"],enemy_shot.message["x"])

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
            if player.number == 0:
                self.token_keeper = player

    def drop_nodes(self, to_drop, players):
        active_players = [p for p in players if p not in to_drop]
        droped_players = []
        
        if len(active_players) == 1:
            print("Seems like you are the only one survived")
            self.players = [self.myself]
            return to_drop
        
        for p in to_drop:
            if self.HANDLE_TIMEOUT_DROP_NODE(p, active_players):
                droped_players.append(p)
        
        return droped_players
        
    def get_next_player_to_play(self):
        return self.get_player_with_player_id(self.get_next_active_player_id(self.token_keeper))
        
    def get_next_active_player_id(self, previous_player):        
        nums = [p.number for p in self.players]
        nums.sort()
        
        for n in nums:
            if n > previous_player.number:
                return n
                
        return nums[0]
    
    def filter_players_by_id(self, removable_id):
        return [player for player in self.players if player.number != removable_id]
    
    def get_player_with_player_id(self, id):
        return next((player for player in self.players if player.number == id), None)
        
    def to_my_turn(self):
        if self.token_keeper.number <= self.myself.number:
            return self.myself.number - self.token_keeper.number
        else:
            return self.myself.number + len(self.players) - self.token_keeper.number
            
    def skip_turn(self):
        if len(self.players) == 1:
            #you are the only one left
            return
        
        if self.token_keeper == self.myself:
            self.play_turn()
        else:
            self.wait_for_turn()

    def start_game(self):
        self.generate_own_board();
        self.generate_board_for_players();

        # Initiator or host will start the game
        if self.own_id == 0:
            self.ui.display_message("Multicasting START_GAME")
            json_players = [p.toJSON() for p in self.players]
            command = {"message": "START_GAME", "players": json_players}
            
            if self.command_loop(command, "ACK_START_GAME", self.players):
                self.ui.display_message("game started by you...")
                self.play_turn()
            else:
                self.ui.display_message("failed to start a game...")
                return False
            
        while len(self.players) > 1:
            self.wait_for_turn()
            if self.token_keeper.number == self.own_id:
                self.play_turn()

        
    def wait_for_turn(self):
        self.ui.display_message("Waitin my turn to play...")
        enemy_shooting_result = self.listen_loop("PLAY_TURN", 30 + 10*self.to_my_turn())
        
        if enemy_shooting_result == None:
            self.skip_turn()
        else:    
            # Who gets the token next
            token_result = self.listen_loop("PASS_TOKEN")
            
            if token_result == None:
                self.skip_turn()
            else:
                # Set the new token owner. Is this the right place? very good question...
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
                    shot_result = self.listen_loop("MOVE_RESULT")
                    
                    if shot_result == None:
                        self.skip_turn()
                    else:    
                        if shot_result.message["result"] == "HIT":
                            mark_shot(self.enemy_boards[enemy_shooting_result.message["target_id"]],enemy_shooting_result.message["y"],enemy_shooting_result.message["x"], HIT)
                        elif shot_result.message["result"] == "MISS":
                            mark_shot(self.enemy_boards[enemy_shooting_result.message["target_id"]],enemy_shooting_result.message["y"],enemy_shooting_result.message["x"], MISS)

        
    def play_turn(self):
        # Check own status
        if all_ships_shot(self.own_board):
            print("TODO: start LOST protocol")
            pass
        elif len(self.players) == 1:
            #you are the only one left
            return
        else:
            # Get next player and their board
            next_player = self.get_next_player_to_play()
            enemy_board = self.enemy_boards[next_player.number]

            # May have to try a couple of times to hit the board or unshot space
            while True:
                # Start the UDP listener in a separate thread to handle timeouts while waiting for input
                event = threading.Event()
                listen_process = threading.Thread(target=self.listen_loop, args=("", 7, event), daemon=True)
                listen_process.start()
                
                self.ui.display_message("OWN BOARD")
                self.ui.render_board(self.own_board)
                self.ui.display_message("ENEMY BOARD")
                self.ui.render_board(enemy_board)
                y = self.ui.request_numeric_input("Enter row: ")
                x = self.ui.request_numeric_input("Enter column: ")
                
                # set the stop event and wait for a thread to end
                event.set()
                listen_process.join()

                # Can't shoot off the board
                if not can_shoot(y, x):
                    self.ui.display_message("Invalid coordinates.")
                    continue

                # Optional: allow trying again if shooting an already shot space
                if already_shot(y, x, enemy_board):
                    self.ui.display_message("You already shot here.")
                    continue

                # Commit to the shot
                self.PLAY_TURN(x, y)
                break   

    def handle_message(self, result, message_to_listen, timer, event):
        print("handle_message...", result.message)
        
        # stop a thread with event
        if not event is None and event.is_set():
            return None
        
        if result.status == Status.OK:
            if result.ip in [p.ip for p in self.players]:
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
                        result = self.HANDLE_RECEIVED_TIMEOUT(result)
                        
                        if result is None:
                            return self.listen_loop(message_to_listen, timer, event)
                        else: 
                            return self.handle_message(result, message_to_listen, timer, event)
                        
                    elif result.message['message'] == 'ELECTION':
                        result = self.HANDLE_RECEIVED_ELECTION(result, timer)
                        
                        if result is None:
                            return self.listen_loop(message_to_listen, timer, event)
                        elif result == True:
                            return None
                        else: 
                            return self.handle_message(result, message_to_listen, timer, event)
                            
                    elif 'repeated' in result.message and result.message['repeated'] == 1:
                        # hope you've heard it already and listening for the next one
                        for p in self.players:
                            if p.ip == result.ip:
                                message = result.message
                                
                                if 'token' in message:
                                    del message['token']
                                self.messaging_service.send_to((p.ip, p.port), message)
                                break
                                
                        return self.listen_loop(message_to_listen, timer, event)
                        
                    else:
                        print("unhandled result:", result.message['message'])
                        return result
                        
                else:
                    print("received result without a message")
                    return result
            
            else:
                print("received multicast from wrong ip:", result.ip)
                return self.listen_loop(message_to_listen, timer, event)
                
        elif result.status == Status.UNHANDELED_TIMEOUT:
            if(self.myself != self.token_keeper):
                result = self.HANDLE_TIMEOUT_TOKEN_LOST()
                
                if result == True:
                    return None
                else:
                    return self.listen_loop(message_to_listen, timer, event)
            else:
                return self.listen_loop(message_to_listen, timer, event)
            
        else:
            print("got unhandled error status in listen loop")
            return result
                
    def listen_loop(self, message_to_listen, timer=6, event=None):
        
        # stop a thread with event
        if not event is None and event.is_set():
            return None
    
        print("listen_loop...", message_to_listen)
        return self.handle_message(self.messaging_service.listen_multicast(timer), message_to_listen, timer, event)
        
    def command_loop(self, command, ack_message, receivers, repeated_times = 0):

        if len(receivers) == 1:
            return True # everybody is dropped in receivers list
            
        if repeated_times > 3:
            return False # somebody is NAK:ing on everything, TODO: force drop
        
        if 'message' not in command:
            print("There should be a message in command:", command)
            return False
            
        if repeated_times > 0:
            command['repeated'] = 1
        
        self.messaging_service.send_to_many(command)
        not_acked = self.messaging_service.collect_acks(receivers, self.myself, ack_message)
        
        if len(not_acked) == 0:
            return True
        else:
            droped_players = self.drop_nodes(not_acked, receivers)
            self.players = [p for p in self.players if p not in droped_players]
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
                    self.players = [self.map_player_from_json(player) for player in result.message['players'] if not self.map_player_from_json(player) is None]
                    myself = [p for p in self.players if p.ip == self.messaging_service.messaging_client.IP]
                    self.set_host_as_token_holder()
                    self.own_id = myself[0].toJSON()["id"]
                    if len(myself) == 1:
                        self.myself = myself[0]
                        self.messaging_service.send_to(
                            (result.ip, port), 
                            {"message": "ACK_START_GAME"})
                        self.start_game()
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
    def PLAY_TURN(self, x, y):
        self.ui.display_message("Sending for shot coordinates via multicast...")
        next_player = self.get_next_player_to_play()
        shot_command = {"target_id": next_player.number, "message": "PLAY_TURN", "x": x, "y": y}

        # Inform shots
        if self.command_loop(shot_command, "PLAY_TURN", self.players):
        
            if len(self.players) == 1:
                #you are the only one left
                return
                
            self.ui.display_message("Sending info or next token holder via multicast...")
            next_player = self.get_next_player_to_play()
            token_command = {"message": "PASS_TOKEN", "id": next_player.number}
            result = self.command_loop(token_command, "PASS_TOKEN", self.players)
            
            if result:
                if len(self.players) == 1:
                    #you are the only one left
                    return
            
                # TODO: get direct port
                self.messaging_service.send_to((next_player.ip, 5005), {"message": "PASS_TOKEN_CONFIRMED"})
                self.token_keeper = next_player
                shot_result = self.listen_loop("MOVE_RESULT")
                
                if shot_result == False:
                    self.skip_turn()
                else:
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


    def HANDLE_TIMEOUT_DROP_NODE(self, player, active_players):
        print("Sending TIMEOUT", player.ip)
        
        if len(active_players) < 2: # only you are active
            self.players = [self.myself]
            return True
            
        # not a command_loop because of NAK handling
        self.messaging_service.send_to_many({"message": "TIMEOUT", "ip": player.ip})
        
        five_sec_timer = time.time() + 5
        ackd_players = [self.myself]
        
        while time.time() < five_sec_timer and len(ackd_players) < len(active_players):
            time_left = five_sec_timer - time.time()
            result = self.messaging_service.listen_broadcast(time_left)
            
            if result.status == Status.OK and result.message["message"] == "TIMEOUT":
                ackd_players.extend(filter(lambda p: p.ip == result.ip, active_players))
            elif result.status == Status.OK and result.message["message"] == "NAK" and result.ip == player.ip:
                return False
            else:
                pass
                
        if len(ackd_players) == len(active_players):
            command = {"message": "DROP", "ip": player.ip}
            
            if self.command_loop(command, "DROP", ackd_players):
                self.players = [p for p in self.players if p != player]
                return True
            else:
                if len(self.players) == 1:
                    #you are the only one left
                    return True
                # Implement handling for non-happy paths
                print("Not everybody ACKed on DROP")
                pass
        else:
            # Implement handling for non-happy paths
            print("Not everybody ACKed on TIMEOUT")
            pass
            
        return False
     
    def HANDLE_RECEIVED_TIMEOUT(self, result):
    
        if result.message['ip'] == self.messaging_service.messaging_client.IP:
            message = {"message": "NAK"}
        else:
            message = {"message": "TIMEOUT", "ip": result.message['ip']}
            
        self.messaging_service.send_to((self.token_keeper.ip, self.token_keeper.port), message)
        result = self.listen_loop("DROP")
        
        if result.status == Status.OK and result.message['message'] == "DROP":
            self.players = [p for p in self.players if p.ip != result.message['ip']]
        else: 
            return result
        
        return None
        # continue the game
        
    def HANDLE_TIMEOUT_TOKEN_LOST(self):
        self.ui.display_message("Sending ELECTION")
        
        # not a command_loop because of NAK handling
        self.messaging_service.send_to_many({"message": "ELECTION"})
        
        five_sec_timer = time.time() + 5
        ackd_players = [self.myself]
        
        while time.time() < five_sec_timer and len(ackd_players) < len(self.players):
            time_left = five_sec_timer - time.time()
            result = self.messaging_service.listen_broadcast(time_left)
            
            if result.status == Status.OK and result.message["message"] == "ACK_ELECTION":
                ackd_players.extend(filter(lambda p: p.ip == result.ip, self.players))
            elif result.status == Status.OK and result.message["message"] == "NAK" and result.ip == self.token_keeper.ip:
                return False
            else:
                pass
                
        if len(ackd_players) == 1:
            # you are the only one left
            self.players = ackd_players
            return True
                
        if len(ackd_players) == len(self.players) - 1:
            command = {"message": "DROP", "ip": self.token_keeper.ip}
            
            if self.command_loop(command, "DROP", ackd_players):
            
                if len(self.players) == 1:
                    #you are the only one left
                    return True
                    
                self.players = [p for p in self.players if p != self.token_keeper]
                next_player = self.get_next_player_to_play()
                message = {"message": "PASS_TOKEN", "id": next_player.number}
                
                if self.command_loop(message, "PASS_TOKEN", self.players):
                    if next_player != self.myself and len(self.players) != 1:
                        self.messaging_service.send_to((next_player.ip, 5005), {"message": "PASS_TOKEN_CONFIRMED"})
                    self.token_keeper = next_player
                    return True
                else:
                    # Implement handling for non-happy paths
                    print("Not everybody ACKed on PASS_TOKEN")
                    pass
            else:
                # Implement handling for non-happy paths
                print("Not everybody ACKed on DROP")
                pass
        else:
            # Implement handling for non-happy paths
            print("Not everybody ACKed on ELECTION")
            pass
            
        return False
        
    def HANDLE_RECEIVED_ELECTION(self, result, timer=6):
        
        for p in self.players:
            if p.ip == result.ip:
                sender = p
                break
                
        if self.token_keeper == self.myself:
            message = {"message": "NAK"}
            self.messaging_service.send_to((sender.ip, sender.port), message)
            return None
        
        message = {"message": "ACK_ELECTION"}
        self.messaging_service.send_to((sender.ip, sender.port), message)
        result = self.listen_loop("DROP", timer)
        
        if result.status == Status.OK and result.message['message'] == "DROP":
            self.players = [p for p in self.players if p.ip != result.message['ip']]
        else: 
            return result
        
        # TODO: change token owner
        result = self.listen_loop("PASS_TOKEN")
        
        if result.status == Status.OK and result.message['message'] == "PASS_TOKEN":
            next_to_play = self.get_player_with_player_id(int(result.message['id']))
            self.token_keeper = next_to_play
            return True
        
        return None
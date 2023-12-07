import json 
import time

from models.NetworkResult import NetworkResult, Status

class MessagingService:
    def __init__(self, messaging_client):
        self.messaging_client = messaging_client
        
    def fun():
        # just to mock timeout handling
        pass
    
    def listen(self, timeout=5.0, HANDLE_TIMEOUT=None):
        (status, data, (ip, port)) = self.messaging_client.listen(timeout, HANDLE_TIMEOUT)
        message = json.loads(data)
        
        result = NetworkResult(status, ip, port, message)
        print("Got direct message:", result.status, result.ip, result.port, result.message)
        
        return result
    
    def listen_broadcast(self, timeout=5.0, HANDLE_TIMEOUT=None):
        (status, data, (ip, port)) = self.messaging_client.listen_broadcast(timeout, HANDLE_TIMEOUT)
        json_dictonary = json.loads(data)
        
        result = NetworkResult(status, ip, port, json_dictonary)            
        print("Got broadcast message:", result.status, result.ip, result.port, result.message)
            
        return result
        
    def listen_multicast(self, timeout=5.0, HANDLE_TIMEOUT=None):
        (status, data, (ip, port)) = self.messaging_client.listen_multicast(timeout, HANDLE_TIMEOUT)
        message = json.loads(data)
        
        result = NetworkResult(status, ip, port, message)            
        print("Got multicast message:", result.status, result.ip, result.port, result.message)
            
        return result
        
    def broadcast(self, message):
        # TODO: Error handling?
        message = json.dumps(message)
        # TODO: Generate id for the message
        self.messaging_client.broadcast(message)
        
        
    def send_to(self, recipient, message):
        # Recipients implies tuple with at least (IP, PORT)
        # TODO: Generate id for the message
        message = json.dumps(message)
        self.messaging_client.send_to(recipient, message)
        
    def send_to_many(self, message):
        # TODO: Generate id for the message
        message = json.dumps(message)
        self.messaging_client.send_to_many(message)
        
    def collect_acks(self, players, myself, ack_message, timer=5):
        n_sec_timer = time.time() + int(timer)
        ackd_players = [myself]
        
        while time.time() < n_sec_timer and len(ackd_players) < len(players):
            time_left = n_sec_timer - time.time()
            result = self.listen_broadcast(time_left)
            
            if result.status == Status.OK and result.message["message"] == ack_message:
                ackd_players.extend(filter(lambda p: p.ip == result.ip, players))
            elif result.status == Status.UNHANDELED_TIMEOUT:
                return [p for p in players if p not in ackd_players]
            else:
                print("exception on collect_ack")
                pass
        
        return []
        
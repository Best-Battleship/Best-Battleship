import json 

from models.NetworkResult import NetworkResult

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
        print("listen result:", result.status, result.ip, result.port, result.message)
        
        return result
    
    def listen_broadcast(self, timeout=5.0, HANDLE_TIMEOUT=None):
        (status, data, (ip, port)) = self.messaging_client.listen_broadcast(timeout, HANDLE_TIMEOUT)
        json_dictonary = json.loads(data)
        
        result = NetworkResult(status, ip, port, json_dictonary)            
        print("broadcast result:", result.status, result.ip, result.port, result.message)
            
        return result
        
    def listen_multicast(self, timeout=5.0, HANDLE_TIMEOUT=None):
        (status, data, (ip, port)) = self.messaging_client.listen_multicast(timeout, HANDLE_TIMEOUT)
        message = json.loads(data)
        
        result = NetworkResult(status, ip, port, message)            
        print("multicast result:", result.status, result.ip, result.port, result.message)
            
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

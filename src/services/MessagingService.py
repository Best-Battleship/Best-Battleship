import json 

class MessagingService:
    def __init__(self, messaging_client):
        self.messaging_client = messaging_client
        
    def fun():
        # just to mock timeout handling
        pass
        
    def listen(self, timeout=5.0, HANDLE_TIMEOUT=fun):
        (data, author) = self.messaging_client.listen(timeout, HANDLE_TIMEOUT)
        message = json.loads(data)
        message = ( message, author )
        
        return message
    
    def listen_broadcast(self, timeout=5.0, HANDLE_TIMEOUT=fun):
        (data, (ip, port)) = self.messaging_client.listen_broadcast(timeout, HANDLE_TIMEOUT)
        json_dictonary = json.loads(data)
        
        if len(json_dictonary) > 0:
            message = ( json_dictonary, (ip, port) )
        else:
        # on timeout after handling
            message = ( json_dictonary, (ip, port) )
            
        return message
        
    def listen_multicast(self, timeout=5.0, HANDLE_TIMEOUT=fun):
        (data, author) = self.messaging_client.listen_multicast(timeout, HANDLE_TIMEOUT)
        message = json.loads(data)
        message = ( message, author )
        return message
        
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

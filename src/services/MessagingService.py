import json 

class MessagingService:
    def __init__(self, messaging_client):
        self.messaging_client = messaging_client
        
    def listen(self):
        message = self.messaging_client.listen()
        message = json.load(message)
        return message
    
    def listen_broadcast(self):
        message = self.messaging_client.listen_broadcast()
        message = json.load(message)
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
        self.messaging_client.send_to_one(recipient, message)
        
    def send_to_many(self, message):
        # TODO: Generate id for the message
        message = json.dumps(message)
        self.messaging_client.send_to_many(message)
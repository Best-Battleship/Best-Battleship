class MessagingService:
    def __init__(self, messaging_client):
        self.messaging_client = messaging_client
        
    def wait(self):
        #TODO: Wait for any messages
        #TODO: Parse JSON message
        message = self.messaging_client.wait()
        return message
        
    def send_to_network(self, message):
        # TODO: Generate id for the message
        # TODO: Create a JSON message
        self.messaging_client.broadcast(message)
        
    def send_to(self, recipients, message):
        # Recipients implies tuples with at least (IP, PORT)
        # TODO: Generate id for the message
        # TODO: Create a JSON message
        self.messaging_client.send_to(recipients, message)
        
    def send_to_and_wait_for_responses(self, recipients, message):
        # TODO: Timeout handling
        # TODO: Generate id for the message
        # TODO: Parse JSON message
        message_id = None
        self.messaging_client.send_to(recipients, message)
        responses = self.messaging_client.wait_for(message_id)
        return responses
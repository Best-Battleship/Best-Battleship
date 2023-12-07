class Player:

    def __init__(self, player_id, ip, broadcast_port):
        self.number = player_id
        self.ip = ip
        self.port = int(broadcast_port)
        
    def toJSON(self):
        return {"id": self.number, 
            "ip": self.ip, 
            "broadcast_port": self.port}

class Player:

    def __init__(self, player_id, ip, direct_port, broadcast_port):
        self.number = player_id
        self.ip = ip
        self.direct_port = int(direct_port)
        self.broadcast_port = int(broadcast_port)
        
    def toJSON(self):
        return {"id": self.number, 
            "ip": self.ip, 
            "direct_port": self.direct_port,
            "broadcast_port": self.broadcast_port}

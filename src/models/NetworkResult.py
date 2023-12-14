import json
from enum import Enum

class Status(Enum):
    INVALID = 0
    OK = 1
    UNHANDELED_ERROR = 2
    HANDELED_ERROR = 3
    UNHANDELED_TIMEOUT = 4
    
class NetworkResult:

    def __init__(self, status = Status.INVALID, ip="0", port=0, message=json.loads("{}") ):
        if status in Status:
            self.status = status
        else:
            try:
                self.status = Status(int(status))
            except:
                self.status = Status.INVALID
                
        self.ip = ip
        self.port = int(port)
        self.message = message
        

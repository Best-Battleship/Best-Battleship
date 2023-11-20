import socket
import json
import struct
import random

# Global variables for netowrking part
MULTICAST_GRP = "224.1.1.1"  # Example multicast group
MULTICAST_PORT = 5007
GAME_PORT = 12345  # Game communication port
BUFFER_SIZE = 1024


# Function to send UDP multicast
def send_multicast(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(json.dumps(msg).encode(), (MULTICAST_GRP, MULTICAST_PORT))


if __name__ == "__main__":
    msg = {"type": "JOIN_GAME", "turn": 2, "content": "board changes"}
    send_multicast(msg)

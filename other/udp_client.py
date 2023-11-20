import socket
import json
import struct

# Global variables for netowrking part
MULTICAST_GRP = "224.1.1.1"  # Example multicast group
MULTICAST_PORT = 5007
GAME_PORT = 12345  # Game communication port
BUFFER_SIZE = 1024


# Function to listen for UDP multicast
def listen_for_multicast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", MULTICAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        message_type, turn, message_content = json.loads(data.decode()).values()
        print(
            f"Received UDP {message_type} message: {message_content} from {addr}, now it's turn {turn}"
        )


if __name__ == "__main__":
    listen_for_multicast()

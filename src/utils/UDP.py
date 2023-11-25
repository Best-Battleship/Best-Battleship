import socket
import struct

# you can use whatever ports
# they just should be different
# broadcast, multicast and p2p
PORT = 5005
PORTB = 5006
PORTM = 5007

BROADCAST_IP = "192.168.1.255" # my home LAN with mask 255.255.255.0
MULTICAST_GRP = "224.1.1.1" # https://en.wikipedia.org/wiki/Multicast_address

def init(ip):
    sock = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM) # UDP
    sock.bind((ip, PORT))
    
    sock_b = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM) # UDP
    sock_b.bind(('', PORTB))
    
    sock_m = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM, # UDP
        socket.IPPROTO_UDP)
    sock_m.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_m.bind((MULTICAST_GRP, PORTM)) # if any windows node, set multicast group to '' on all nodes
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GRP), socket.INADDR_ANY)
    sock_m.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    return (sock, sock_b, sock_m)

def send(sock, ip, port, m):
    # comment away next line on windows node 
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
    sock.sendto(m.encode('utf-8'), (ip, port))

def broadcast(sock_b, m):
    # comment away next line on windows node 
    sock_b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock_b.sendto(m.encode('utf-8'), (BROADCAST_IP, PORTB))
    
def multicast(sock_m, m):
    sock_m.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2) # idk, read ttl maybe
    sock_m.sendto(m.encode('utf-8'), (MULTICAST_GRP, PORTM))

def listen(sock):
    data, addr = sock.recvfrom(1024)
    print("received on listen:", data)
    
def listen_broadcast(sock):
    data, addr = sock.recvfrom(1024)
    print("received on broadcasst listen:", data)
    # return to send response
    return addr
    
def listen_multicast(sock):
    data, addr = sock.recvfrom(1024)
    print("received on multicast listen:", data)
    
    return addr


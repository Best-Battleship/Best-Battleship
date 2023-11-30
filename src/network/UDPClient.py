import socket
import struct

class UDPClient:
    BROADCAST_IP = "192.168.1.255" # my home LAN with mask 255.255.255.0
    MULTICAST_GRP = "224.1.1.1" # https://en.wikipedia.org/wiki/Multicast_address
    
    def __init__(self, IP, PORT, PORTB, PORTM):
        ## Socket initialization
        self.sock = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_DGRAM) # UDP
        self.sock.bind((IP, PORT))
        
        self.sock_b = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_DGRAM) # UDP
        self.sock_b.bind(('', PORTB))
        
        self.sock_m = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_DGRAM, # UDP
            socket.IPPROTO_UDP)
        self.sock_m.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_m.bind((self.MULTICAST_GRP, PORTM)) # if any windows node, set multicast group to '' on all nodes
        mreq = struct.pack("4sl", socket.inet_aton(self.MULTICAST_GRP), socket.INADDR_ANY)
        self.sock_m.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
    # Public interface, implement by utilizing the private functions
        
    def send_to_network(self, message):
        print("TODO: broadcast message in network")
        
    def send_to_one(self, recipient, message):
        print("TODO: send message to 1 (IP, PORT) tuple")
        
    def send_to_many(self, recipients, message):
        print("TODO: send message to 1..n (IP, PORT) tuple")
        
    def wait_for_responses(self, id_answered_to, n):
        print("TODO: wait for n answers with given id")
        
    def wait(self):
        print("TODO: Wait for any messages")
        
    ## Private methods

    def __send(self, ip, port, m):
        # comment away next line on windows node 
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
        self.sock.sendto(m.encode('utf-8'), (ip, port))

    def __broadcast(self, m):
        # comment away next line on windows node 
        self.sock_b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock_b.sendto(m.encode('utf-8'), (self.BROADCAST_IP, self.PORTB))
        
    def __multicast(self, m):
        self.sock_m.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2) # idk, read ttl maybe
        self.sock_m.sendto(m.encode('utf-8'), (self.MULTICAST_GRP, self.PORTM))

    def __listen(self):
        data, addr = self.sock.recvfrom(1024)
        print("received on listen:", data)
        
    def __listen_broadcast(self):
        data, addr = self.sock_B.recvfrom(1024)
        print("received on broadcasst listen:", data)
        # return to send response
        return addr
        
    def __listen_multicast(self):
        data, addr = self.sock_m.recvfrom(1024)
        print("received on multicast listen:", data)
        
        return addr
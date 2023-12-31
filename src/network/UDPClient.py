import socket
import struct

from models.NetworkResult import Status

class UDPClient:
    BROADCAST_IP = "255.255.255.255" # absolute
    MULTICAST_GRP = "224.1.1.1" # https://en.wikipedia.org/wiki/Multicast_address
    
    def __init__(self, PORT, PORTB, PORTM, IP=None):
        self.PORT = PORT
        self.PORTB = PORTB
        self.PORTM = PORTM
        ## Socket initialization
        if IP is None:
            self.direct_socket_initialized = False
        else:
            self.init_direct_port(IP)
        
        self.sock_b = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_DGRAM) # UDP
        self.sock_b.bind(('', PORTB))
        
        self.sock_m = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_DGRAM, # UDP
            socket.IPPROTO_UDP)
        self.sock_m.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Windows
        # self.sock_m.bind(('', PORTM))
        
        # Others
        self.sock_m.bind((self.MULTICAST_GRP, PORTM))
        
        mreq = struct.pack("4sl", socket.inet_aton(self.MULTICAST_GRP), socket.INADDR_ANY)
        self.sock_m.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
    def init_direct_port(self, own_ip = 0, server_ip = "192.168.1.1"):
        if own_ip == 0:
            IP = socket.gethostbyname(socket.gethostname())
        else:    
            IP = own_ip
            
        if IP.startswith("127.0."):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try: s.connect((server_ip, 80))
            except: pass
            IP = s.getsockname()[0]
            s.close()
        
        self.IP = IP
        self.sock = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_DGRAM) # UDP
        self.sock.bind((IP, self.PORT))
        self.direct_socket_initialized = True
                
    # Public interface, implement by utilizing the private functions
        
    def broadcast(self, message):
        self.__broadcast(message)
        
    def send_to(self, recipient, message):
        (ip, port) = recipient
        self.__send(ip, port, message)
        
    def send_to_many(self, message):
        self.__multicast(message)
        
    def wait_for_responses(self, id_answered_to, n, timeout):
        print("TODO: wait for n answers with given id")
        
    def listen(self, timeout):
        # author is (ip, port)
        (status, data, author) = self.__listen(timeout)
        return (status, data, author)
        
    def listen_broadcast(self, timeout):
        # author is (ip, port)
        (status, data, author) = self.__listen_broadcast(timeout)
        return (status, data, author)
            
    def listen_multicast(self, timeout):
        # author is (ip, port)
        (status, data, author) = self.__listen_multicast(timeout)
        return (status, data, author)
        
    ## Private methods

    def __send(self, ip, port, m):
        # comment away next line on windows node 
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
        self.sock.sendto(m.encode('utf-8'), (ip, port))

    def __broadcast(self, m):
        # comment away next line on windows node 
        self.sock_b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock_b.sendto(m.encode('utf-8'), (self.BROADCAST_IP, self.PORTB))
                
        try:
            self.sock_b.settimeout(1.0)
            data, addr = self.sock_b.recvfrom(1024) # catch own broadcast
            ip, port = addr
            
            if not self.direct_socket_initialized:
                self.init_direct_port(ip)
        except socket.timeout:
            print("Your broadcast is configured wrong")
        finally:
            self.sock_b.settimeout(None)
        
    def __multicast(self, m):
        self.sock_m.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2) # idk, read ttl maybe
        self.sock_m.sendto(m.encode('utf-8'), (self.MULTICAST_GRP, self.PORTM))
                
        try:
            self.sock_m.settimeout(1.0)
            self.sock_m.recvfrom(1024) # catch own multicast
        except socket.timeout:
            print("Your multicast is configured wrong")
        finally:
            self.sock_m.settimeout(None)

    def __listen(self, timeout):
        self.sock.settimeout(timeout)
        
        try:
            data, addr = self.sock.recvfrom(1024)
            self.sock.settimeout(None)
            return (Status.OK, data, addr)
        except socket.timeout:
            self.sock.settimeout(None)          
            return (Status.UNHANDELED_TIMEOUT, "{}", (0, 0))
            
    def __listen_broadcast(self, timeout):
        self.sock_b.settimeout(timeout)
        
        try:
            data, addr = self.sock_b.recvfrom(1024)
            self.sock_b.settimeout(None)
            ip, port = addr
            
            if not self.direct_socket_initialized:
                self.init_direct_port(0, ip)
            
            return (Status.OK, data, addr)
        except socket.timeout:
            self.sock_b.settimeout(None)           
            return (Status.UNHANDELED_TIMEOUT, "{}", (0, 0))
            
    def __listen_multicast(self, timeout):
        self.sock_m.settimeout(timeout)
        
        try:
            data, addr = self.sock_m.recvfrom(1024)
            self.sock_m.settimeout(None) 
            return (Status.OK, data, addr)
        except socket.timeout:
            self.sock_m.settimeout(None) 
            return (Status.UNHANDELED_TIMEOUT, "{}", (0, 0))

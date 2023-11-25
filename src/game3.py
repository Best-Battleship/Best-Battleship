from utils.UDP import *

(sock, sock_b, sock_m) = init("192.168.1.5") # put your own ip
initiator = input("initiate or wait (i/w): ")

if initiator == "i":
    broadcast(sock_b, "INIT_GAME")
    listen_broadcast(sock_b) # catch own broadcast
    players = []
    
    # TODO: timer here
    while len(players) < 2: # exactly 3 nodes playing, change
        player = (ip, port) = listen_broadcast(sock_b)
        send(sock, ip, port, "ACK_JOIN")
        players.append(player)
        print(players)

    multicast(sock_m, "START_GAME")
    listen_multicast(sock_m) # catch own multicast
    
    for i in range(len(players)):
        listen_broadcast(sock_b) # listen to all income UDP for ACK
        
    input("game started by you...")

else:
    initiator_addr = (ip, port) = listen_broadcast(sock_b)
    send(sock, ip, port, "JOIN_GAME")
    listen(sock)
    
    initiator_addr = (ip, m_port) = listen_multicast(sock_m)
    send(sock, ip, port, "ACK") # answer on broadcast port, otherwise imposible
    input("game sarted...")

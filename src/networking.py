import random
import socket
import json
import random
import threading


# Function to send UDP multicast
def send_multicast(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(message.encode(), (MULTICAST_GRP, MULTICAST_PORT))


# Function to listen for UDP multicast
def listen_for_multicast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", MULTICAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        # Handle received data
        handle_multicast_data(data.decode(), addr)


def send_udp_message(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(message.encode(), (ip, port))


def handle_multicast_data(data, addr):
    message_type, message_content = json.loads(data).values()
    print(f"Received multicast message: {data} from {addr}")

    if message_type == "INIT_GAME":
        # Join the game if it's a new game initialization message
        # Here you could add logic to prevent joining an already started game
        join_game_as_player(addr[0])  # addr[0] contains the IP of the initiator


def udp_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("", GAME_PORT))
        while True:
            data, addr = s.recvfrom(BUFFER_SIZE)
            handle_udp_message(data.decode(), addr)


# Function to handle incoming TCP connections
def handle_udp_message(data, addr):
    message_type, message_content = json.loads(data).values()
    print(f"Received UDP message: {data} from {addr}")


# # Modify handle_client to handle different types of messages
# def handle_client(client_socket, addr):
#     while True:
#         try:
#             data = client_socket.recv(BUFFER_SIZE).decode()
#             if data:
#                 message_type, message_content = json.loads(data).values()
#                 # Add your message handling logic here
#                 if message_type == "JOIN_GAME":
#                     # Handle a player joining the game
#                     # ...
#                 elif message_type == "START_GAME":
#                     # Handle the start of the game
#                     # ...
#                 # Add more conditions for other message types
#         except ConnectionError:
#             # Handle connection errors
#             break


def handle_init_game_organizer():
    # Send JOIN_GAME to all connected players using UDP
    for player in players:
        send_udp_message(
            player["ip"], GAME_PORT, json.dumps({"type": "JOIN_GAME", "content": None})
        )
    # Wait for ACK_JOIN from all players and then send START_GAME using UDP
    # ...


def handle_init_game_player(data, organizer_ip):
    # Logic for handling INIT_GAME message as a player using UDP
    send_udp_message(
        organizer_ip, GAME_PORT, json.dumps({"type": "JOIN_GAME", "content": None})
    )
    # ...


# Implement start_game_as_initiator
def start_game_as_initiator(player_board):
    global current_turn, players
    current_turn = 0  # Initiator starts
    players.append((0, "initiator_ip"))  # Add initiator with ID 0

    send_multicast(json.dumps({"type": "INIT_GAME", "content": None}))
    place_all_ships(player_board)
    # Wait for players to join (e.g., based on a specific time or number of players)
    # ...
    # After players have joined, send START_GAME message
    for player in players:
        send_tcp_message(
            player["ip"], GAME_PORT, json.dumps({"type": "START_GAME", "content": None})
        )


# Implement join_game_as_player
def join_game_as_player(organizer_ip):
    # Connect to the organizer and send a JOIN_GAME message
    send_tcp_message(
        organizer_ip, GAME_PORT, json.dumps({"type": "JOIN_GAME", "content": None})
    )
    # Wait for START_GAME message before starting the game
    # ...


def broadcast_board_state(board):
    """Broadcast the initial or updated board state to all players."""
    board_state = {"type": "BOARD_UPDATE", "content": board}
    send_multicast(json.dumps(board_state))


def update_all_players():
    """Send the latest board state to all players."""
    global current_turn, players

    for player_id, player_ip in players:
        updated_data = {
            "board": player_board,  # Or only send necessary changes
            "current_turn": current_turn,
        }
        send_udp_message(player_ip, GAME_PORT, json.dumps(updated_data))
    current_turn = (current_turn + 1) % len(players)


def wait_for_turn():
    global current_turn, players
    while True:
        data, addr = receive_udp_message()
        message_type, message_content = json.loads(data).values()

        if (
            message_type == "TURN_UPDATE"
            and message_content["current_turn"] == get_my_player_id()
        ):
            update_board_state(message_content["board"])
            current_turn = get_my_player_id()
            break
        elif message_type == "BOARD_UPDATE":
            update_board_state(message_content)


def is_my_turn():
    global current_turn
    return current_turn == get_my_player_id()


def get_my_player_id():
    # Assuming the player's IP is known (e.g., 'my_ip')
    # Find and return the player's ID based on their IP
    for player_id, player_ip in players:
        if player_ip == my_ip:
            return player_id
    return None


def receive_udp_message():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("", GAME_PORT))  # Bind to the game port
        data, addr = s.recvfrom(BUFFER_SIZE)
        return data.decode(), addr

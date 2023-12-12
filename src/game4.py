from ui.CLI import CLI
from domain.Game import Game
from services.MessagingService import MessagingService
from network.UDPClient import UDPClient
from sys import argv

IP = None
START_MODE = None

try:
    START_MODE = argv[1]
except IndexError:
    pass
try:
    IP = argv[2]
except IndexError:
    pass

PORT = 5005 # TODO Ask for these? What if in use?
PORTB = 5006
PORTM = 5007
ui = CLI()
messaging_client = UDPClient(PORT, PORTB, PORTM, IP)
messaging_service = MessagingService(messaging_client)
game = Game(ui, messaging_service)

ui.print_boxed_text("Welcome to Best Battleship!")
while True:
    if START_MODE != None:
        if START_MODE == "H":
            game.create_game()
            break
        elif START_MODE == "C":
            game.wait_for_a_game()
            break
    wants_to_init = ui.request_text_input("Do you want to start a new game? Yes or no? Empty input quits: ").lower()
    if wants_to_init == "yes":
        game.create_game()
        break
    elif wants_to_init == "no":
        game.wait_for_a_game()
        break
    elif wants_to_init == "":
        break
    else:
        ui.display_message("You did not give a proper value.")
        continue
    
ui.display_message("Bye!")

    
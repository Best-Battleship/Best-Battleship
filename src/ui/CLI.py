class CLI:
    def display_message(self, message):
        print(message)
    
    def request_numeric_input(self, question):
        value = None
        while True:
            try:
                value = int(input(question))
            except ValueError:
                print("Please try again. Give a number.")
                continue
            else:
                break
        return value
    
    def request_text_input(self, question):
        value = input(question)
        return value
    
    def render_board(self, board):
        for row in board:
            print(' '.join(row))
            print()
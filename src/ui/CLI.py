class CLI:
    def display_message(self, message):
        box_width = 120
        inner_width = box_width - 4 
        print(f"* {message.center(inner_width)} *")

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

    def print_boxed_text(self, text):
        box_width = 120
        inner_width = box_width - 4 
        print('*' * box_width)
        print(f"* {text.center(inner_width)} *")

        print('*' * box_width)
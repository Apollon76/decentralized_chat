from src import packet


class Log:
    def __init__(self, file_name: str):
        self.file_name = file_name
        try:
            with open(file_name, 'w') as f:
                f.write('log started\n')
        except FileNotFoundError:
            print("Can't open file for logging.")
        self.messages = []

    def get(self, message: packet.Packet):
        self.messages.append(message)
        self.save(message)

    def save(self, message: packet.Packet):
        with open(self.file_name, 'a') as f:
            print(repr(message), file=f)

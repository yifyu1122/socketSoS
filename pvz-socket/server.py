import socket
import threading
import json

class GameServer:
    def __init__(self, host='localhost', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        self.clients = []
        self.game_state = {
            'plants': [],
            'zombies': []
        }
        print(f'Server started on {host}:{port}')

    def handle_client(self, client_socket, addr):
        print(f'Connection from {addr} has been established.')
        self.clients.append(client_socket)

        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.process_message(message)
                self.broadcast_game_state()
            except ConnectionResetError:
                break

        client_socket.close()
        self.clients.remove(client_socket)
        print(f'Connection from {addr} has been closed.')

    def process_message(self, message):
        data = json.loads(message)
        if data['type'] == 'plant':
            self.game_state['plants'].append(data['plant'])
        elif data['type'] == 'zombie':
            self.game_state['zombies'].append(data['zombie'])

    def broadcast_game_state(self):
        state_json = json.dumps(self.game_state)
        for client in self.clients:
            client.send(state_json.encode('utf-8'))

    def start(self):
        while True:
            client_socket, addr = self.server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()

if __name__ == '__main__':
    game_server = GameServer()
    game_server.start()
import socket
import json

def main():
    # Connect to the server
    server_address = ('localhost', 65432)  # Change to your server's address and port
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    try:
        while True:
            # Get user input for zombie placement
            x = int(input("Enter the x position to place the zombie (0-9): "))
            y = int(input("Enter the y position to place the zombie (1-6): "))

            # Create a message to send to the server
            message = {
                'action': 'place_zombie',
                'position': (x, y)
            }

            # Send the message to the server
            client_socket.sendall(json.dumps(message).encode('utf-8'))

            # Wait for the server's response
            response = client_socket.recv(1024).decode('utf-8')
            print("Server response:", response)

    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
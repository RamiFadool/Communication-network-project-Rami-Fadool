import socket
import os
from app_config import APP_SERVER_HOST, TCP_SERVER_PORT, BUFFER_SIZE, FILES_FOLDER


def main():
    # create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind server to host and port
    server_socket.bind((APP_SERVER_HOST, TCP_SERVER_PORT))

    server_socket.listen(5)
    print("TCP server started")
    print(f"Listening on {APP_SERVER_HOST}:{TCP_SERVER_PORT}...")

    while True:
        # accept connection from client
        client_socket, client_address = server_socket.accept()
        print("Client connected:", client_address)

        # receive request from client
        request = client_socket.recv(BUFFER_SIZE).decode()
        print("Received request:")
        print(request)

        # if nothing was received, close connection
        if not request:
            client_socket.close()
            print("Empty request!")
            continue

        # split the request into parts
        request_parts = request.split()

        # check if the request format is valid
        if len(request_parts) < 2 or request_parts[0] != "GET":
            response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid request"
            client_socket.send(response.encode())
            client_socket.close()
            print("Sent 400 Bad Request")
            continue

        # get the file name
        file_name = request_parts[1].lstrip("/")

        # build full path to the file
        file_path = os.path.join(FILES_FOLDER, file_name)

        # check if file exists
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                file_data = file.read()

            response = "HTTP/1.1 200 OK\r\n\r\n" + file_data
            client_socket.send(response.encode())
            print(f"Sent file: {file_name}")

        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\nFile not found"
            client_socket.send(response.encode())
            print(f"File not found: {file_name}")

        # close connection 
        client_socket.close()
        print("Connection closed\n")


if __name__ == "__main__":
    main()
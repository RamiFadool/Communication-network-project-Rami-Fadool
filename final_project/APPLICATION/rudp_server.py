import socket
import json
import os
import random

from app_config import (
    APP_SERVER_HOST,
    RUDP_SERVER_PORT,
    BUFFER_SIZE,
    FILES_FOLDER,
    TIMEOUT,
    CHUNK_SIZE
)


def main():
    # create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # bind server to host and port
    server_socket.bind((APP_SERVER_HOST, RUDP_SERVER_PORT))

    # set timeout for waiting for ACK messages
    server_socket.settimeout(TIMEOUT)

    print("RUDP server started")
    print(f"Listening on {APP_SERVER_HOST}:{RUDP_SERVER_PORT}...")

    while True:
        try:
            # receive request from client
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            # no request arrived yet
            continue

        try:
            # convert bytes to dictionary
            message = json.loads(data.decode())
        except json.JSONDecodeError:
            print("Received invalid JSON message")
            continue

        print("Received from client:", message)

        # client asks to download a file
        if message.get("type") == "GET_FILE":
            file_name = message.get("file_name")
            file_path = os.path.join(FILES_FOLDER, file_name)

            # check if the file exists
            if not os.path.exists(file_path):
                error_message = {
                    "type": "ERROR",
                    "message": "File not found"
                }

                server_socket.sendto(json.dumps(error_message).encode(), client_address)
                print("File not found")
                continue

            # read the file content
            with open(file_path, "r", encoding="utf-8") as file:
                file_data = file.read()

            # split file into smaller chunks
            chunks = []
            for i in range(0, len(file_data), CHUNK_SIZE):
                chunks.append(file_data[i:i + CHUNK_SIZE])

            seq = 0

            # stop and wait: send each chunk and wait for ACK before sending the next one
            for chunk in chunks:
                packet = {
                    "type": "DATA",
                    "seq": seq,
                    "data": chunk,
                    "last": False
                }

                while True:
                    if random.random() < 0.2:
                        print(f"Simulated loss of packet {seq}")
                    else:
                        server_socket.sendto(json.dumps(packet).encode(), client_address)
                        print(f"Sent packet {seq}")

                    try:
                        ack_data, _ = server_socket.recvfrom(BUFFER_SIZE)
                        ack_message = json.loads(ack_data.decode())

                        if ack_message.get("type") == "ACK" and ack_message.get("seq") == seq:
                            print(f"Received ACK for packet {seq}")
                            break

                    except socket.timeout:
                        print(f"Timeout on packet {seq}, sending again...")

                seq += 1

            # send final packet (file finished))
            end_packet = {
                "type": "DATA",
                "seq": seq,
                "data": "",
                "last": True
            }

            while True:
                if random.random() < 0.2:
                        print(f"Simulated loss of last packet {seq}")
                else:
                    server_socket.sendto(json.dumps(end_packet).encode(), client_address)
                    print("Sent last packet")

                try:
                    ack_data, _ = server_socket.recvfrom(BUFFER_SIZE)
                    ack_message = json.loads(ack_data.decode())

                    if ack_message.get("type") == "ACK" and ack_message.get("seq") == seq:
                        print("Received ACK for last packet")
                        break

                except socket.timeout:
                    print("Timeout on last packet, sending again...")


if __name__ == "__main__":
    main()
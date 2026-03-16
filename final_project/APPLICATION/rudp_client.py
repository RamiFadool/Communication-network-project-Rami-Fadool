import socket
import json
from app_config import (
    APP_SERVER_HOST,
    RUDP_SERVER_PORT,
    BUFFER_SIZE,
    DEFAULT_FILE_NAME
)


def main():
    # create UDP socket for the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # address of the RUDP server
    server_address = (APP_SERVER_HOST, RUDP_SERVER_PORT)

    # this will keep the file data in the correct order
    full_file_data = ""

    # the client expects packets in order: 0, 1, 2, ...
    expected_seq = 0

    try:
        # send request to download the file
        request_message = {
            "type": "GET_FILE",
            "file_name": DEFAULT_FILE_NAME
        }

        client_socket.sendto(json.dumps(request_message).encode(), server_address)
        print("Client sent file request")

        while True:
            # receive packet from server
            data, _ = client_socket.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode())

            print("Client received:", message)

            # check if server returned an error
            if message.get("type") == "ERROR":
                print("Server error:", message.get("message"))
                break

            # process file data packets
            if message.get("type") == "DATA":
                seq = message.get("seq")
                chunk_data = message.get("data")
                is_last = message.get("last")

                # accept only the expected packet number
                if seq == expected_seq:
                    full_file_data += chunk_data

                    ack_message = {
                        "type": "ACK",
                        "seq": seq
                    }

                    client_socket.sendto(json.dumps(ack_message).encode(), server_address)
                    print(f"Sent ACK for packet {seq}")

                    expected_seq += 1

                    # if this is the last packet, stop receiving
                    if is_last:
                        print("Received last packet")
                        break

                else:
                    # send ACK again for the last correct packet if needed
                    ack_message = {
                        "type": "ACK",
                        "seq": expected_seq - 1
                    }

                    client_socket.sendto(json.dumps(ack_message).encode(), server_address)
                    print("Received unexpected packet number")

        # save the downloaded file
        downloaded_file_name = "downloaded_" + DEFAULT_FILE_NAME
        with open(downloaded_file_name, "w", encoding="utf-8") as file:
            file.write(full_file_data)

        print(f"\nFile downloaded successfully: {downloaded_file_name}")

    except Exception as e:
        print("An error happened:", e)

    finally:
        client_socket.close()
        print("Connection closed")


if __name__ == "__main__":
    main()
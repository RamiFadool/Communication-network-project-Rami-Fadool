import socket
import json
from dhcp_config import (
    DHCP_SERVER_HOST,
    DHCP_SERVER_PORT,
    BUFFER_SIZE,
    OFFERED_IP,
    DNS_SERVER_IP,
    SUBNET_MASK,
    GATEWAY
)


def main():
    # create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # bind the socket to the server address and port from the config file
    server_socket.bind((DHCP_SERVER_HOST, DHCP_SERVER_PORT))

    print("DHCP server started")
    print(f"Listening on {DHCP_SERVER_HOST}:{DHCP_SERVER_PORT}...")

    # this variable keeps the last IP that was offered
    last_offered_ip = None

    while True:
        # wait for a packet from client
        data, client_address = server_socket.recvfrom(BUFFER_SIZE)

        try:
            # decode and convert from JSON text to a dictionary
            message = json.loads(data.decode())
        except json.JSONDecodeError:
            print("Received invalid JSON message")
            continue

        msg_type = message.get("type")
        client_id = message.get("client_id")

        print("Received from client:", message)

        # check client id (to identify and request a specifec IP address)
        if client_id is None:
            print("ERROR: Message doesn't contain client_id")
            continue

        # the client asks for IP address
        if msg_type == "DISCOVER":
            last_offered_ip = OFFERED_IP

            offer_message = {
                "type": "OFFER",
                "client_id": client_id,
                "ip": OFFERED_IP,
                "dns": DNS_SERVER_IP,
                "subnet_mask": SUBNET_MASK,
                "gateway": GATEWAY
            }

            # send the offer back to the client
            server_socket.sendto(json.dumps(offer_message).encode(), client_address)
            print(f"Sent OFFER to {client_id}")

        # the client asks to receive the offered IP
        elif msg_type == "REQUEST":
            requested_ip = message.get("ip")

            # make sure the client asks for the IP that was offered
            if requested_ip != last_offered_ip:
                error_message = {
                    "type": "ERROR",
                    "message": "Requested IP doesn't match the offered IP"
                }

                server_socket.sendto(json.dumps(error_message).encode(), client_address)
                print(f"Client {client_id} requested a different IP")
                continue

            ack_message = {
                "type": "ACK",
                "client_id": client_id,
                "ip": requested_ip,
                "dns": DNS_SERVER_IP,
                "subnet_mask": SUBNET_MASK,
                "gateway": GATEWAY
            }

            # ACK = server approves
            server_socket.sendto(json.dumps(ack_message).encode(), client_address)
            print(f"Sent ACK to {client_id}")

        else:
            print("Unknown message type")


if __name__ == "__main__":
    main()
import socket
import json
from dns_config import DNS_SERVER_HOST, DNS_SERVER_PORT, BUFFER_SIZE, DOMAIN_NAME, DOMAIN_IP


def main():
    # create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # bind server to host and port
    server_socket.bind((DNS_SERVER_HOST, DNS_SERVER_PORT))

    print("DNS server started")
    print(f"Listening on {DNS_SERVER_HOST}:{DNS_SERVER_PORT}...")

    while True:
        # receive data from client
        data, client_address = server_socket.recvfrom(BUFFER_SIZE)

        try:
            # convert bytes to dictionary
            message = json.loads(data.decode())
        except json.JSONDecodeError:
            print("Received invalid JSON message")
            continue

        msg_type = message.get("type")
        domain = message.get("domain")

        print("Received from client:", message)

        # check if the client sent a domain name
        if domain is None:
            error_message = {
                "type": "DNS_ERROR",
                "message": "No domain was sent"
            }
            server_socket.sendto(json.dumps(error_message).encode(), client_address)
            print("Client didn't send a domain name")
            continue

        # client asks for the IP address of a domain
        if msg_type == "DNS_QUERY":
            if domain == DOMAIN_NAME:
                response_message = {
                    "type": "DNS_RESPONSE",
                    "domain": domain,
                    "ip": DOMAIN_IP
                }

                server_socket.sendto(json.dumps(response_message).encode(), client_address)
                print("Sent DNS response to client")

            else:
                error_message = {
                    "type": "DNS_ERROR",
                    "message": "Domain not found"
                }

                server_socket.sendto(json.dumps(error_message).encode(), client_address)
                print("Domain was not found")

        else:
            print("ERROR: Unknown message type")


if __name__ == "__main__":
    main()
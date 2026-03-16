import socket
import json
from dhcp_config import DHCP_SERVER_HOST, DHCP_SERVER_PORT, BUFFER_SIZE


def main():
    # create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # address of the DHCP server
    server_address = (DHCP_SERVER_HOST, DHCP_SERVER_PORT)

    # simple id for this client
    client_id = "rami1"

    try:
        # send DISCOVER message
        discover_message = {
            "type": "DISCOVER",
            "client_id": client_id
        }

        client_socket.sendto(json.dumps(discover_message).encode(), server_address)
        print("Client sent DISCOVER")

        # receive the OFFER message from the server
        data, _ = client_socket.recvfrom(BUFFER_SIZE)
        offer_message = json.loads(data.decode())

        print("Client received:", offer_message)

        # if the server returns an error, stop
        if offer_message.get("type") == "ERROR":
            print("Server error:", offer_message.get("message"))
            return

        # check if server answered with OFFER
        if offer_message.get("type") != "OFFER":
            print("Error: server did not send OFFER")
            return

        offered_ip = offer_message.get("ip")

        # check if the server offered an IP address
        if offered_ip is None:
            print("Error: OFFER message doesn't contain an IP address")
            return

        # send REQUEST for the IP that was offered
        request_message = {
            "type": "REQUEST",
            "client_id": client_id,
            "ip": offered_ip
        }

        client_socket.sendto(json.dumps(request_message).encode(), server_address)
        print("Client sent REQUEST")

        # receive the answer from the server
        data, _ = client_socket.recvfrom(BUFFER_SIZE)
        ack_message = json.loads(data.decode())

        print("Client received:", ack_message)

        # if the server returns an error, stop
        if ack_message.get("type") == "ERROR":
            print("Server error:", ack_message.get("message"))
            return

        # ACK so the DHCP process finished successfully
        if ack_message.get("type") == "ACK":
            print("\nDHCP process completed successfully")
            print("Assigned IP:", ack_message.get("ip"))
            print("DNS Server:", ack_message.get("dns"))
            print("Subnet Mask:", ack_message.get("subnet_mask"))
            print("Default Gateway:", ack_message.get("gateway"))
        else:
            print("Error: DHCP process failed")

    except Exception as e:
        print("An error happened:", e)

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
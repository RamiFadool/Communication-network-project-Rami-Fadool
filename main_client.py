import socket
import json

# import DHCP config
from DHCP.dhcp_config import (
    DHCP_SERVER_HOST,
    DHCP_SERVER_PORT,
    BUFFER_SIZE as DHCP_BUFFER
)

# import DNS config
from DNS.dns_config import (
    DNS_SERVER_HOST,
    DNS_SERVER_PORT,
    BUFFER_SIZE as DNS_BUFFER,
    DOMAIN_NAME
)

# import Application config
from APPLICATION.app_config import (
    TCP_SERVER_PORT,
    RUDP_SERVER_PORT,
    BUFFER_SIZE as APP_BUFFER,
    DEFAULT_FILE_NAME
)


def run_dhcp():
    # create a UDP socket for DHCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_address = (DHCP_SERVER_HOST, DHCP_SERVER_PORT)

    try:
        # send DISCOVER message to DHCP server
        discover_message = {
            "type": "DISCOVER",
            "client_id": "main_client"
        }

        client_socket.sendto(json.dumps(discover_message).encode(), server_address)
        print("\n[DHCP] Sent DISCOVER")

        # receive OFFER from server
        data, _ = client_socket.recvfrom(DHCP_BUFFER)
        offer_message = json.loads(data.decode())

        print("[DHCP] Received:", offer_message)

        if offer_message.get("type") != "OFFER":
            print("[DHCP] Error: server did not send OFFER")
            return None

        offered_ip = offer_message.get("ip")

        # send REQUEST for the offered IP
        request_message = {
            "type": "REQUEST",
            "client_id": "main_client",
            "ip": offered_ip
        }

        client_socket.sendto(json.dumps(request_message).encode(), server_address)
        print("[DHCP] Sent REQUEST")

        # receive ACK from server
        data, _ = client_socket.recvfrom(DHCP_BUFFER)
        ack_message = json.loads(data.decode())

        print("[DHCP] Received:", ack_message)

        # stop if server returned an error
        if ack_message.get("type") == "ERROR":
            print("[DHCP] Server error:", ack_message.get("message"))
            return None
        
        if ack_message.get("type") == "ACK":
            print("[DHCP] Configuration completed successfully")

            return {
                "ip": ack_message.get("ip"),
                "dns": ack_message.get("dns"),
                "subnet_mask": ack_message.get("subnet_mask"),
                "gateway": ack_message.get("gateway")
            }

        else:
            print("[DHCP] ERROR: DHCP process failed")
            return None

    except Exception as e:
        print("[DHCP] ERROR:", e)
        return None

    finally:
        client_socket.close()


def run_dns():
    # create a UDP socket for DNS
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_address = (DNS_SERVER_HOST, DNS_SERVER_PORT)

    try:
        # send DNS query for the domain name
        query_message = {
            "type": "DNS_QUERY",
            "domain": DOMAIN_NAME
        }

        client_socket.sendto(json.dumps(query_message).encode(), server_address)
        print("\n[DNS] Sent DNS query")

        # receive response from DNS server
        data, _ = client_socket.recvfrom(DNS_BUFFER)
        response = json.loads(data.decode())

        print("[DNS] Received:", response)

        if response.get("type") == "DNS_ERROR":
            print("[DNS] DNS query failed")
            print("[DNS] Reason:", response.get("message"))
            return None
        
        if response.get("type") == "DNS_RESPONSE":
            print("[DNS] DNS process completed successfully")
            return response.get("ip")
        else:
            print("[DNS] DNS query failed")
            print("[DNS] Reason:", response.get("message"))
            return None

    except Exception as e:
        print("[DNS] ERROR:", e)
        return None

    finally:
        client_socket.close()


def download_with_tcp(server_ip):
    # create a TCP socket for the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connect to the TCP application server
        client_socket.connect((server_ip, TCP_SERVER_PORT))
        print(f"\n[TCP] Connected to server {server_ip}:{TCP_SERVER_PORT}")

        # build a HTTP GET request
        request = f"GET /{DEFAULT_FILE_NAME} HTTP/1.1\r\nHost: {server_ip}\r\n\r\n"

        # send the request to the server
        client_socket.send(request.encode())
        print("[TCP] Sent request to server")

        # receive the full response from the server
        response = b""
        while True:
            part = client_socket.recv(APP_BUFFER)
            if not part:
                break
            response += part

        # convert bytes to text
        response_text = response.decode()
        print("[TCP] Received response from server")

        # split the response into header and body (html parts)
        parts = response_text.split("\r\n\r\n", 1)

        if len(parts) < 2:
            print("[TCP] Invalid response from server")
            return

        header = parts[0]
        body = parts[1]

        # check if server returned the file successfully
        if "200 OK" in header:
            downloaded_file_name = "downloaded_tcp_" + DEFAULT_FILE_NAME

            # save the downloaded file
            with open(downloaded_file_name, "w", encoding="utf-8") as file:
                file.write(body)

            print(f"[TCP] File downloaded successfully: {downloaded_file_name}")
        else:
            print("[TCP] The server didn't return the file successfully")

    except Exception as e:
        print("[TCP] ERROR:", e)

    finally:
        client_socket.close()
        print("[TCP] Connection closed")


def download_with_rudp(server_ip):
    # create a UDP socket for the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_address = (server_ip, RUDP_SERVER_PORT)

    # this will keep the file data in the correct order
    full_file_data = ""

    # the client expects packets in order: 0, 1, 2, ...
    expected_seq = 0

    download_success = False

    try:
        # send request to download the file
        request_message = {
            "type": "GET_FILE",
            "file_name": DEFAULT_FILE_NAME
        }

        client_socket.sendto(json.dumps(request_message).encode(), server_address)
        print(f"\n[RUDP] Sent file request to {server_ip}:{RUDP_SERVER_PORT}")

        while True:
            # receive packet from server
            data, _ = client_socket.recvfrom(APP_BUFFER)
            message = json.loads(data.decode())

            print("[RUDP] Received:", message)

            # check if server returned an error
            if message.get("type") == "ERROR":
                print("[RUDP] Server error:", message.get("message"))
                return

            # process data packets
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
                    print(f"[RUDP] Sent ACK for packet {seq}")

                    expected_seq += 1

                    # if this is the last packet, stop receiving
                    if is_last:
                        print("[RUDP] Received last packet")
                        download_success = True
                        break

                else:
                    # send ACK again for the last correct packet
                    ack_message = {
                        "type": "ACK",
                        "seq": expected_seq - 1
                    }

                    client_socket.sendto(json.dumps(ack_message).encode(), server_address)
                    print("[RUDP] Received unexpected packet number")

        # save the downloaded file
        if download_success:
            downloaded_file_name = "downloaded_rudp_" + DEFAULT_FILE_NAME
            with open(downloaded_file_name, "w", encoding="utf-8") as file:
                file.write(full_file_data)
            print(f"[RUDP] File downloaded successfully: {downloaded_file_name}")
        else:
            print("[RUDP] File download didn't finish successfully")

    except Exception as e:
        print("[RUDP] ERROR:", e)

    finally:
        client_socket.close()
        print("[RUDP] Connection closed")


def main():
    print("Choose how you want to download the file:")
    print("1 - TCP")
    print("2 - Reliable UDP")

    choice = input("Enter your choice: ")

    if choice == "1":
        print("You chose TCP")
    elif choice == "2":
        print("You chose Reliable UDP")
    else:
        print("Invalid choice")
        return

    # 1) get network configuration from DHCP
    dhcp_data = run_dhcp()

    if dhcp_data is None:
        print("Couldn't continue because DHCP failed")
        return

    print("\nClient network configuration:")
    print("Client IP:", dhcp_data["ip"])
    print("DNS Server:", dhcp_data["dns"])
    print("Subnet Mask:", dhcp_data["subnet_mask"])
    print("Default Gateway:", dhcp_data["gateway"])

    # 2) ask the DNS server for the website IP
    server_ip = run_dns()

    if server_ip is None:
        print("Couldn't continue because DNS failed")
        return

    print("\nThe domain was resolved successfully")
    print("Domain:", DOMAIN_NAME)
    print("Server IP:", server_ip)

    # 3) download the file using the chosen protocol
    if choice == "1":
        download_with_tcp(server_ip)
    else:
        download_with_rudp(server_ip)


if __name__ == "__main__":
    main()
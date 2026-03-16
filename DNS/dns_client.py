import socket
import json
from dns_config import DNS_SERVER_HOST, DNS_SERVER_PORT, BUFFER_SIZE, DOMAIN_NAME


def main():
    # create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # address of the DNS server
    server_address = (DNS_SERVER_HOST, DNS_SERVER_PORT)

    try:
        # send DNS query for the domain name
        query_message = {
            "type": "DNS_QUERY",
            "domain": DOMAIN_NAME
        }

        client_socket.sendto(json.dumps(query_message).encode(), server_address)
        print("Client sent DNS query")

        # receive response from the server
        data, _ = client_socket.recvfrom(BUFFER_SIZE)
        response = json.loads(data.decode())

        print("Client received:", response)

        # check if the server returned an error
        if response.get("type") == "DNS_ERROR":
            print("DNS query failed")
            print("Reason:", response.get("message"))
            return
        
        # check if the server returned the IP address
        if response.get("type") == "DNS_RESPONSE":
            if response.get("ip") is None:
                print("DNS response does not contain an IP address")
                return
            print("\nDNS process completed successfully")
            print("Domain name:", response.get("domain"))
            print("IP address:", response.get("ip"))

        else:
            print("DNS query failed")
            print("Reason:", response.get("message"))

    except Exception as e:
        print("ERROR:", e)

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
import socket
from app_config import APP_SERVER_HOST, TCP_SERVER_PORT, BUFFER_SIZE, DEFAULT_FILE_NAME


def main():
    # create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to the application server
    client_socket.connect((APP_SERVER_HOST, TCP_SERVER_PORT))
    print("Connected to TCP server")

    # build a HTTP GET request
    request = f"GET /{DEFAULT_FILE_NAME} HTTP/1.1\r\nHost: {APP_SERVER_HOST}\r\n\r\n"

    # send the request to the server
    client_socket.send(request.encode())
    print("Sent request to server")

    # receive the full response from the server
    response = b""
    while True:
        part = client_socket.recv(BUFFER_SIZE)
        if not part:
            break
        response += part

    # convert bytes to text
    response_text = response.decode()
    print("Received response from server:\n")
    print(response_text)

    # split the response into header and body (html parts)
    parts = response_text.split("\r\n\r\n", 1)

    if len(parts) < 2:
        print("Invalid response from server")
        client_socket.close()
        return

    header = parts[0]
    body = parts[1]

    # check if server returned the file successfully
    if "200 OK" in header:
        downloaded_file_name = "downloaded_" + DEFAULT_FILE_NAME

        # save the downloaded file
        with open(downloaded_file_name, "w", encoding="utf-8") as file:
            file.write(body)

        print(f"\nFile downloaded successfully: {downloaded_file_name}")
    else:
        print("\nThe server didn't return the file successfully")

    # close the connection
    client_socket.close()
    print("Connection closed")


if __name__ == "__main__":
    main()
import socket

def connect_and_send_messages():
    # Setup connection details
    host = 'localhost'
    port = 2000
    
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connect to server
        client_socket.connect((host, port))
        
        # List of messages to send
        messages = [
            "HELO",
            "MAIL FROM:test@test.com",
            "RCPT TO:lander@email.com",
            "DATA",
            "From: test@test.com\n",
            "To: lander@email.com\n",
            "Subject: Test mail\n",
            "Received: 00:00:00\n",
            "Hello this is a test mail.\n",
            "\n.\n",
        ]
        
        # Loop through messages, send them and wait for a response
        for message in messages:
            # Send message
            client_socket.sendall(message.encode('utf-8'))
            print(f"Sent: {message}")
            
            # Receive response from server
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Received: {response}")
            print("--------------------------------------")

if __name__ == "__main__":
    connect_and_send_messages()

import socket
import datetime
import argparse

port = 2000

def connect_and_send_messages():
    # Setup connection details
    host = 'localhost'
    
    
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
            f"Received: {datetime.datetime.now().strftime('%Y-%m-%d : %H : %M')}\n",
            "Hello this is a test mail.\n",
            "RSET\n",
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


# class MailOption():
#     def handleInput(conn):
#         return

def getOption(prompt):
    while True:
        user_input = input(prompt)
        try:
            value = int(user_input)
            if value not in [1,2,3,4]:
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


def sendMail(conn):
    run = True
    while run:
        user_input = input("Client: ") + '\n'
        conn.sendall(user_input.encode('utf-8'))

        response = conn.recv(1024).decode('utf-8')
        print("Server: " + response)
        
        if("message accepted for delivery" in response):
            print("MAIL FULLY RECEIVED")
            run = False

def menu(conn):
    run = True
    while run:
        print("What would you like to do?")
        print("1) Mail Sending")
        print("2) Mail Managment")
        print("3) Mail Searching")
        print("4) EXIT")
        option = getOption("Enter an integer (1-4): ")
        print("You chose:", option)

        if option == 1:
            print("SENDING MAIL")
            print("-------------------------------")
            sendMail(conn)
        elif option > 1:
            print("NOT IMPLEMENTED YET!")



def main():
    parser = argparse.ArgumentParser(description="The adress of the SMPTY and POP3 server")
    parser.add_argument('adress', type=str, help='A string as adress')
    args = parser.parse_args()
    print(args.adress)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connect to server
        client_socket.connect((args.adress, port))

        menu(client_socket)

if __name__ == "__main__":
    main()

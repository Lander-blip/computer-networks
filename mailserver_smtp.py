import argparse
import socket

users = ["lander@email.com", "robbe@email.com"]
receivingMail = None

class Mail:
    def __init__(self, sender):
        self.sender = sender
        self.rcpts = []
        self.receivedDataCMD = False
        self.body = ""
        self.bodyComplete = False
        self.time = ""
        self.subject = ""

    def __str__(self):
        msg = "From: " + self.sender + '\n'
        msg += "To: " + str(self.rcpts) + '\n'
        msg += "Subject: " + self.subject + '\n'
        # msg += "Received" + self.time + '\n'
        msg += self.body + '\n'
        return msg

    def addRcpt(self, rcpt):
        if (rcpt in self.rcpts or self.receivedDataCMD): #cant add rcpts when starting to receive the body
            return
        self.rcpts.append(rcpt)

    def startReceivingData(self):
        self.receivedDataCMD = True

    def appendToBody(self, msg):
        self.body += msg

        chunks = msg.split('\n')
        #filter metadata
        for chunk in chunks:
            if "Subject: " in chunk:
                self.subject = chunk[len("Subject: "):]

        if (self.body[-3:] == "\n.\n"):
            self.bodyComplete = True
            self.body = self.body[:-3]
            return True
        return False


def send(connection, msg):
    connection.sendall(msg.encode())

def handleCommand(connection, data):
    global receivingMail
    cmd = data.replace('\n', "")
    if (cmd == "HELO"):
        print("Sending HELO back")
        send(connection, "250 OK")

    if ("MAIL FROM:" in cmd):
        mail = cmd[len("MAIL FROM:"):]
        if("@" in mail): #correct email
            send(connection, "250 OK")
            receivingMail = Mail(mail)
        else:
            send(connection, "501, incorrect mailadress")

    if(not receivingMail):
        return

    if("RCPT TO:" in cmd):
        mail = cmd[len("RCPT TO:"):]
        if mail in users:
            receivingMail.addRcpt(mail)
            send(connection, "250 OK")
        else:
            send(connection, "550 No such user here")

    if (cmd == "DATA"):
        receivingMail.startReceivingData()
        send(connection, "354 Start mail input; end with <CRLF>.<CRLF>")
        return

    if(receivingMail.receivedDataCMD): #add received data to the body of the mail
        if(receivingMail.appendToBody(data)):
            print("RECEIVED MAIL, READY TO SAVE MAIL!")
            send(connection, "250 OK, message accepted for delivery")
        else:
            send(connection, "200 OK, received correctly")
            #write message in correct subfolder

    print("CURRENT RECEIVED EMAIL:")
    print(receivingMail)
    print("------------------------------")


def main():
    parser = argparse.ArgumentParser(description="Start a TCP server that listens for connections on a specified port.")
    parser.add_argument('port', type=int, help='An integer for the port number')
    args = parser.parse_args()

    # Create a socket object using TCP / IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the server address and port number
    server_address = ('localhost', args.port)
    print(f"Starting up on {server_address[0]} port {server_address[1]}")
    server_socket.bind(server_address)

    # Listen for incoming connections (server mode)
    server_socket.listen(5)
    print("Waiting for a connection...")

    try:
        # Wait for a connection
        connection, client_address = server_socket.accept()
        print(f"Connection from {client_address} has been established.")
        
        # The following loop will echo back any received data to the client
        while True:
            data = connection.recv(1024)
            if data:
                print("Received data:", repr(data.decode()))
                handleCommand(connection, data.decode())
            else:
                print("No data received. Closing connection.")
                break
    finally:
        # Clean up the connection
        connection.close()

if __name__ == '__main__':
    main()

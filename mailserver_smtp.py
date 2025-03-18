import argparse
import socket
import os
import threading

# Sample user list (for VRFY command)
users = [("lander", "lander@email.com"),
         ("robbe", "robbe@email.com")]

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
        msg = "From: " + self.sender + "\n"
        msg += "To: " + str(self.rcpts) + "\n"
        msg += "Subject: " + self.subject + "\n"
        msg += self.body + "\n"
        return msg

    def toString(self, mail):
        if mail not in self.rcpts:
            print("ERROR: mailadress not in recipientslist")
            return ""
        newBody = ""
        splitBody = self.body.split("\n")
        for elem in splitBody:
            if "From: " in elem or "To: " in elem:
                continue
            newBody += elem + "\n"
        msg = "From: " + self.sender + "\n"
        msg += "To: " + mail + "\n"
        msg += newBody + "\n"
        return msg

    def addRcpt(self, rcpt):
        if rcpt in self.rcpts or self.receivedDataCMD:
            return
        self.rcpts.append(rcpt)

    def startReceivingData(self):
        self.receivedDataCMD = True

    def appendToBody(self, msg):
        self.body += msg
        chunks = msg.split("\n")
        # Filter metadata to extract subject.
        for chunk in chunks:
            if "Subject: " in chunk:
                self.subject = chunk[len("Subject: "):]
        if self.body[-3:] == "\n.\n":
            self.bodyComplete = True
            self.body = self.body[:-3]
            return True
        return False

def send(connection, msg):
    connection.sendall(msg.encode())
    print("Server:", msg)

def writeMailOnDisk(mail):
    for rcpt in mail.rcpts:
        name = rcpt[:rcpt.find("@")]
        if os.path.exists(name):
            with open(os.path.join(name, "my_mailbox"), "a") as file:
                file.write(mail.toString(rcpt))
        else:
            print(f"ERROR: directory {name} not found")

def handleCommand(connection, data, receivingMail):
    """
    Process a command received from the client.
    The local variable 'receivingMail' is passed in and returned after processing.
    Returns a tuple: (continue_connection (bool), updated_receivingMail)
    """
    cmd = data.replace("\n", "").replace("\r", "")
    if cmd == "HELO":
        send(connection, "250 OK")
        return True, receivingMail

    if "MAIL FROM: <" in cmd:
        mail_addr = cmd[len("MAIL FROM: <"):-1]
        if "@" in mail_addr:
            send(connection, "250 OK")
            receivingMail = Mail(mail_addr)
            return True, receivingMail
        else:
            send(connection, "501, incorrect mailadress")
            return True, receivingMail

    if cmd == "RSET":
        send(connection, "200 Mail resetted")
        receivingMail = None
        return True, receivingMail

    if cmd == "QUIT":
        send(connection, "GOODBYE")
        return False, receivingMail

    if "VRFY " in cmd:
        user = cmd[len("VRFY "):]
        for i in range(len(users)):
            if user == users[i][0] or user == users[i][1]:
                name = users[i][0]
                mail_addr = users[i][1]
                send(connection, f"250 {name} {mail_addr}")
                return True, receivingMail
        send(connection, "550 No such user here")
        return True, receivingMail

    if cmd == "NOOP":
        send(connection, "250 OK")
        return True, receivingMail

    if not receivingMail:
        send(connection, "500 unknown command")
        return True, receivingMail

    if "RCPT TO: <" in cmd:
        mail_addr = cmd[len("RCPT TO: <"):-1]
        if mail_addr in [user[1] for user in users]:
            receivingMail.addRcpt(mail_addr)
            send(connection, "250 OK")
        else:
            send(connection, "550 No such user here")
        return True, receivingMail

    if cmd == "DATA":
        receivingMail.startReceivingData()
        send(connection, "354 Start mail input; end with <CRLF>.<CRLF>")
        return True, receivingMail

    if receivingMail.receivedDataCMD:
        if receivingMail.appendToBody(data):
            send(connection, "250 OK, message accepted for delivery")
            writeMailOnDisk(receivingMail)
            receivingMail = None
        else:
            send(connection, "200 OK, received correctly")
        return True, receivingMail

    return True, receivingMail

def client_thread(connection, client_address):
    receivingMail = None  # Local variable for each connection
    try:
        run = True
        while run:
            data = connection.recv(1024)
            if data:
                decoded = data.decode()
                print("Received data:", repr(decoded))
                run, receivingMail = handleCommand(connection, decoded, receivingMail)
            else:
                print("No data received. Closing connection.")
                break
    finally:
        connection.close()
        print(f"Connection with {client_address} closed.")

def main():
    parser = argparse.ArgumentParser(description="Start a TCP server that listens for connections on a specified port.")
    parser.add_argument('port', type=int, help='An integer for the port number')
    args = parser.parse_args()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', args.port)
    print(f"Starting up on {server_address[0]} port {server_address[1]}")
    server_socket.bind(server_address)
    server_socket.listen(5)
    print("Waiting for connections...")

    try:
        while True:
            connection, client_address = server_socket.accept()
            print(f"Connection from {client_address} has been established.")
            threading.Thread(target=client_thread, args=(connection, client_address)).start()
    finally:
        server_socket.close()

if __name__ == '__main__':
    import threading
    main()

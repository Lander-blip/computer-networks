import argparse
import socket
import os

users = [("lander", "lander@email.com"), ("robbe", "robbe@email.com")]
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

    def toString(self, mail):
        if(mail not in self.rcpts):
            print("ERROR: mailadress not in recipientslist")
            return

        newBody = ""
        splitBody = self.body.split("\n")
        for elem in splitBody:
            if "From: " in elem or "To: " in elem:
                continue
            newBody += elem + '\n'

        msg = "From: " + self.sender + '\n'
        msg += "To: " + mail + '\n'
        msg += newBody + '\n'
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

def writeMailOnDisk(mail):
    for rcpt in mail.rcpts:
        name = rcpt[:rcpt.find("@")]
        if(os.path.exists(name)):
            with open(name + "/" + "my_mailbox", "a") as file:
                file.write(mail.toString(rcpt))
        else:
            print(f"ERROR: directory {name} not found")

def handleCommand(connection, data): #returns False when connection needs to be closed
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

    if (cmd == "RSET"):
        print("resetting current received mail")
        send(connection, "200 Mail resetted")
        receivingMail = None

    if (cmd == "QUIT"):
        print("Quiting... ")
        send(connection, "GOODBYE")
        return False

    if ("VRFY " in cmd): #only works to check for emails in maillist
        user = cmd[len("VRFY "):]
        for i in range(len(users)):
            if(user == users[i][0] or user == users[i][1]):
                name = users[i][0]
                mail = users[i][1]
                send(connection, f"250 {name} {mail}")
                return True
        send(connection, "550 No such user here")

    if (cmd == "NOOP"):
        send(connection, "250 OK")
        return True

    if(not receivingMail):
        return True

    if("RCPT TO:" in cmd):
        mail = cmd[len("RCPT TO:"):]
        if mail in [user[1] for user in users]:
            receivingMail.addRcpt(mail)
            send(connection, "250 OK")
        else:
            send(connection, "550 No such user here")

    if (cmd == "DATA"):
        receivingMail.startReceivingData()
        send(connection, "354 Start mail input; end with <CRLF>.<CRLF>")
        return True

    if(receivingMail.receivedDataCMD): #add received data to the body of the mail
        if(receivingMail.appendToBody(data)):
            print("RECEIVED MAIL, READY TO SAVE MAIL!")
            send(connection, "250 OK, message accepted for delivery")
            writeMailOnDisk(receivingMail)
            receivingMail = None
        else:
            send(connection, "200 OK, received correctly")
            #write message in correct subfolder

    print("CURRENT RECEIVED EMAIL:")
    print(receivingMail)
    print("------------------------------")
    return True


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
        run = True
        while run:
            data = connection.recv(1024)
            if data:
                print("Received data:", repr(data.decode()))
                run = handleCommand(connection, data.decode())
            else:
                print("No data received. Closing connection.")
                break
    finally:
        # Clean up the connection
        connection.close()

if __name__ == '__main__':
    main()

import argparse
import socket
import os
import threading

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
        if (rcpt in self.rcpts or self.receivedDataCMD): # can't add rcpts when starting to receive the body
            return
        self.rcpts.append(rcpt)

    def startReceivingData(self):
        self.receivedDataCMD = True

    def appendToBody(self, msg):
        self.body += msg

        chunks = msg.split('\n')
        # filter metadata
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

def handleCommand(connection, data):  # returns False when connection needs to be closed
    global receivingMail
    cmd = data.replace('\n', "").replace("\r", "")
    if (cmd == "HELO"):
        print("Sending HELO back")
        send(connection, "250 OK")
        return True

    if ("MAIL FROM: <" in cmd):
        mail = cmd[len("MAIL FROM: <"):-1]  # filter out
        if("@" in mail):  # correct email
            send(connection, "250 OK")
            receivingMail = Mail(mail)
            return True
        else:
            send(connection, "501, incorrect mailadress")
            return True

    if (cmd == "RSET"):
        print("resetting current received mail")
        send(connection, "200 Mail resetted")
        receivingMail = None
        return True

    if (cmd == "QUIT"):
        print("Quiting... ")
        send(connection, "GOODBYE")
        return False

    if ("VRFY " in cmd):  # only works to check for emails in mail list
        user = cmd[len("VRFY "):]
        for i in range(len(users)):
            if(user == users[i][0] or user == users[i][1]):
                name = users[i][0]
                mail = users[i][1]
                send(connection, f"250 {name} {mail}")
                return True
        send(connection, "550 No such user here")
        return True

    if (cmd == "NOOP"):
        send(connection, "250 OK")
        return True

    if(not receivingMail):
        send(connection, "500 unknown command")
        return True

    if("RCPT TO: <" in cmd):
        mail = cmd[len("RCPT TO: <"):-1]  # filter out last >
        if mail in [user[1] for user in users]:
            receivingMail.addRcpt(mail)
            send(connection, "250 OK")
        else:
            send(connection, "550 No such user here")

    if (cmd == "DATA"):
        receivingMail.startReceivingData()
        send(connection, "354 Start mail input; end with <CRLF>.<CRLF>")
        return True

    if(receivingMail.receivedDataCMD):  # add received data to the body of the mail
        if(receivingMail.appendToBody(data)):
            print("RECEIVED MAIL, READY TO SAVE MAIL!")
            send(connection, "250 OK, message accepted for delivery")
            writeMailOnDisk(receivingMail)
            receivingMail = None
        else:
            send(connection, "200 OK, received correctly")

    print("CURRENT RECEIVED EMAIL:")
    print(receivingMail)
    print("------------------------------")
    return True

def client_thread(connection, client_address):
    try:
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
            # Start a new thread to handle this connection
            threading.Thread(target=client_thread, args=(connection, client_address)).start()
    finally:
        server_socket.close()

if __name__ == '__main__':
    import threading
    main()

import socket
import getpass

class MailClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.smtp_socket = None
        self.pop3_socket = None
        self.SMTP_PORT = 2000  # Updated to the specified SMTP port
        self.POP3_PORT = 3000  # Updated to the specified POP3 port
        self.username = input("Enter your username: ")
        self.password = getpass.getpass("Enter your password: ")
        self.connect()

    def connect(self):
        self.smtp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.smtp_socket.connect((self.server_ip, self.SMTP_PORT))

    def send_email(self):
        self._receiveSMTP()  # Server greeting

        # Send HELO command
        self._sendSMTP("HELO\n")
        self._receiveSMTP()

        # Send MAIL FROM command
        mail_from = input("From: ")
        self._sendSMTP(f"MAIL FROM: <{mail_from}>\n")
        self._receiveSMTP()

        # Send RCPT TO command
        response = "550"
        while "550" in response:
            to_address = input("To : ")
            self._sendSMTP(f"RCPT TO: <{to_address}>\n")
            response = self._receiveSMTP()

        # Send DATA command
        self._sendSMTP("DATA\n")
        self._receiveSMTP()

        # Send email data
        subject = "Subject: " + input("Subject: ") + '\n'
        #SEND TIMESTAMP TO SERVER
        self._sendSMTP(subject)
        print("Enter message body, end with a line containing only '.':")
        while True:
            line = input() + '\n'
            self._sendSMTP(line)
            if line == ".\n":
                print("EMAIL COMPLETE")
                break;



    def manage_emails(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as pop3_socket:
            pop3_socket.connect((self.server_ip, self.POP3_PORT))
            self._receive()  # Server greeting

            # Authentication
            self._send(f"USER {self.username}\r\n")
            self._receive()
            self._send(f"PASS {self.password}\r\n")
            response = self._receive()
            if "+OK" not in response:
                print("Authentication failed.")
                return

            # List emails
            self._send("LIST\r\n")
            response = self._receive()
            print("Email List:\n", response)

            # Delete an email (optional)
            email_number = input("Enter email number to delete or 'exit' to stop: ")
            if email_number.lower() != 'exit':
                self._send(f"DELE {email_number}\r\n")
                self._receive()

            self._send("QUIT\r\n")
            self._receive()

    def search_emails(self):
        # This method should ideally interact with a search functionality on the server side,
        # which needs to be implemented separately in the POP3 server.
        print("Search functionality needs to be implemented on the server.")

    def _sendSMTP(self, message):
        #print("C: ", message.strip())
        self.smtp_socket.sendall(message.encode())

    def _receiveSMTP(self):
        response = self.smtp_socket.recv(1024).decode()
        #print("S: ", response.strip())
        return response

    def start(self):
        while True:
            print("\n1. Send Email\n2. Manage Emails\n3. Search Emails\n4. Exit")
            choice = input("Choose an option: ")
            if choice == '1':
                self.send_email()
            elif choice == '2':
                self.manage_emails()
            elif choice == '3':
                self.search_emails()
            elif choice == '4':
                print("Exiting.")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    server_ip = input("Enter server IP address: ")
    client = MailClient(server_ip)
    client.start()

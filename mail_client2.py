import socket
import getpass
import datetime

class MailClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.smtp_socket = None
        self.pop3_socket = None
        self.SMTP_PORT = 2000  # Specified SMTP port
        self.POP3_PORT = 3000  # Specified POP3 port
        self.connectSMTP()

    def connectSMTP(self):
        self.smtp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.smtp_socket.connect((self.server_ip, self.SMTP_PORT))

    def connectPOP(self):
        self.pop3_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pop3_socket.connect((self.server_ip, self.POP3_PORT))

    # --------------------------
    # SMTP helper methods
    # --------------------------
    def _sendSMTP(self, message):
        # Uncomment print statements for debugging if needed
        # print("SMTP C: ", message.strip())
        self.smtp_socket.sendall(message.encode())

    def _receiveSMTP(self):
        response = self.smtp_socket.recv(1024).decode()
        # print("SMTP S: ", response.strip())
        return response

    # --------------------------
    # POP3 helper methods
    # --------------------------
    def _sendPOP(self, message):
        # print("POP C: ", message.strip())
        self.pop3_socket.sendall(message.encode())

    def _receivePOP(self, multiline=False):
        if not multiline:
            response = self.pop3_socket.recv(1024).decode()
            # print("POP S: ", response.strip())
            return response
        else:
            # Read lines until termination sequence is detected
            lines = []
            while True:
                chunk = self.pop3_socket.recv(1024).decode()
                lines.append(chunk)
                if "\r\n.\r\n" in chunk or chunk.strip() == ".":
                    break
            return "".join(lines)

    # --------------------------
    # Sending Email (SMTP)
    # --------------------------
    def send_email(self):
        # SMTP interaction
        self._receiveSMTP()  # Read server greeting

        # Send HELO command
        self._sendSMTP("HELO " + self.server_ip + "\r\n")
        self._receiveSMTP()

        # Send MAIL FROM command
        mail_from = input("From: ")
        self._sendSMTP(f"MAIL FROM: <{mail_from}>\r\n")
        self._receiveSMTP()

        # Send RCPT TO command (repeat until no error)
        response = "550"
        while "550" in response:
            to_address = input("To: ")
            self._sendSMTP(f"RCPT TO: <{to_address}>\r\n")
            response = self._receiveSMTP()

        # Send DATA command
        self._sendSMTP("DATA\r\n")
        self._receiveSMTP()

        # Send email headers and body
        subject = "Subject: " + input("Subject: ") + "\r\n"
        timestamp = datetime.datetime.now().strftime("%d %b %Y : %H : %M")
        received_line = f"Received: {timestamp}\r\n"
        self._sendSMTP(subject)
        self._sendSMTP(received_line)
        print("Enter message body, end with a line containing only '.':")
        while True:
            line = input() + "\r\n"
            self._sendSMTP(line)
            if line == ".\r\n":
                print("EMAIL COMPLETE")
                break

        # End DATA with termination sequence
        self._sendSMTP("\r\n.\r\n")
        self._receiveSMTP()

        # Optionally, send QUIT (or keep connection open for further emails)
        self._sendSMTP("QUIT\r\n")
        self._receiveSMTP()

    # --------------------------
    # Managing Emails (POP3)
    # --------------------------
    def manage_emails(self):
        # Connect to POP3 server
        self.connectPOP()
        greeting = self._receivePOP()
        print("POP3 Server:", greeting.strip())

        # Prompt for POP3 credentials (separate from SMTP credentials)
        authenticated = False
        while not authenticated:
            pop_username = input("Enter your POP3 username: ")
            pop_password = getpass.getpass("Enter your POP3 password: ")
            self._sendPOP(f"USER {pop_username}\r\n")
            user_resp = self._receivePOP()
            if not user_resp.startswith("+OK"):
                print("USER command rejected. Try again.")
                continue
            self._sendPOP(f"PASS {pop_password}\r\n")
            pass_resp = self._receivePOP()
            if pass_resp.startswith("+OK"):
                authenticated = True
                print("Authentication successful.")
            else:
                print("Authentication failed. Please try again.")

        # Retrieve and display email summary using LIST
        self._sendPOP("LIST\r\n")
        list_response = self._receivePOP(multiline=True)
        print("\nEmail Summary:")
        print(list_response.strip())
        print("\nEnter POP3 commands to manage your emails.")
        print("Available commands: STAT, LIST, RETR <msg#>, DELE <msg#>, RSET, QUIT")

        # Interactive loop for mail management
        while True:
            command = input("POP3> ").strip()
            if not command:
                continue
            self._sendPOP(command + "\r\n")
            if command.upper().startswith("RETR"):
                resp = self._receivePOP(multiline=True)
            else:
                resp = self._receivePOP()
            print(resp.strip())
            if command.upper() == "QUIT":
                break

        self.pop3_socket.close()

    def search_emails(self):
        print("Search functionality is not implemented on the server.")

    # --------------------------
    # Main Client Loop
    # --------------------------
    def start(self):
        while True:
            print("\nOptions:")
            print("1. Send Email")
            print("2. Manage Emails")
            print("3. Search Emails")
            print("4. Exit")
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

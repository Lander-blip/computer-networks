import socket
import getpass

# SMTP & POP3 Server Configuration
SMTP_PORT = 1025  # Change as needed
POP3_PORT = 1100  # Change as needed

class MailClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.username = None
        self.password = None

    def start(self):
        """Start the client interface."""
        print("Welcome to the Mail Client!")
        self.authenticate()
        while True:
            print("\nOptions:")
            print("1) Send Email")
            print("2) Manage Emails (View & Delete)")
            print("3) Search Emails")
            print("4) Exit")
            choice = input("Select an option: ")

            if choice == "1":
                self.send_email()
            elif choice == "2":
                self.manage_emails()
            elif choice == "3":
                self.search_emails()
            elif choice == "4":
                print("Exiting Mail Client. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    def authenticate(self):
        """Authenticate user with username and password."""
        print("\n--- User Authentication ---")
        self.username = input("Enter your username: ")
        self.password = getpass.getpass("Enter your password: ")
        if not self.validate_login():
            print("Authentication failed. Exiting.")
            exit()

    def validate_login(self):
        """Validate user credentials via POP3 authentication."""
        try:
            pop_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pop_conn.connect((self.server_ip, POP3_PORT))
            pop_conn.recv(1024)  # Receive greeting
            pop_conn.sendall(f"USER {self.username}\r\n".encode())
            response = pop_conn.recv(1024).decode()
            if "+OK" not in response:
                return False
            pop_conn.sendall(f"PASS {self.password}\r\n".encode())
            response = pop_conn.recv(1024).decode()
            if "+OK" not in response:
                return False
            pop_conn.sendall("QUIT\r\n".encode())
            pop_conn.close()
            return True
        except Exception as e:
            print(f"Error during authentication: {e}")
            return False

    def send_email(self):
        """Send an email using SMTP."""
        print("\n--- Sending Email ---")
        sender = f"{self.username}@mailserver.com"
        receiver = input("To: ")
        subject = input("Subject: ")
        print("Enter message body (end with a single '.' on a new line):")
        body = []
        while True:
            line = input()
            if line == ".":
                break
            body.append(line)
        message = f"From: {sender}\r\nTo: {receiver}\r\nSubject: {subject}\r\n\r\n" + "\n".join(body) + "\r\n."

        try:
            smtp_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            smtp_conn.connect((self.server_ip, SMTP_PORT))
            smtp_conn.recv(1024)  # Receive greeting
            smtp_conn.sendall(f"HELO {self.server_ip}\r\n".encode())
            smtp_conn.recv(1024)
            smtp_conn.sendall(f"MAIL FROM: <{sender}>\r\n".encode())
            smtp_conn.recv(1024)
            smtp_conn.sendall(f"RCPT TO: <{receiver}>\r\n".encode())
            smtp_conn.recv(1024)
            smtp_conn.sendall("DATA\r\n".encode())
            smtp_conn.recv(1024)
            smtp_conn.sendall(message.encode() + b"\r\n.\r\n")
            response = smtp_conn.recv(1024).decode()
            if "250 OK" in response:
                print("Mail sent successfully!")
            else:
                print("Failed to send mail.")
            smtp_conn.sendall("QUIT\r\n".encode())
            smtp_conn.close()
        except Exception as e:
            print(f"Error while sending email: {e}")

    def manage_emails(self):
        """View and delete emails using the POP3 server."""
        print("\n--- Managing Emails ---")
        try:
            pop_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pop_conn.connect((self.server_ip, POP3_PORT))
            pop_conn.recv(1024)  # Receive greeting
            pop_conn.sendall(f"USER {self.username}\r\n".encode())
            pop_conn.recv(1024)
            pop_conn.sendall(f"PASS {self.password}\r\n".encode())
            pop_conn.recv(1024)

            pop_conn.sendall("LIST\r\n".encode())
            response = pop_conn.recv(4096).decode()
            print("\nEmails:\n", response)

            while True:
                delete_choice = input("Enter email number to delete (or 'q' to quit): ")
                if delete_choice.lower() == "q":
                    break
                pop_conn.sendall(f"DELE {delete_choice}\r\n".encode())
                print(pop_conn.recv(1024).decode())

            pop_conn.sendall("QUIT\r\n".encode())
            pop_conn.close()
        except Exception as e:
            print(f"Error managing emails: {e}")

    def search_emails(self):
        """Search emails by keyword, time, or sender address."""
        print("\n--- Search Emails ---")
        print("1) Search by Keyword")
        print("2) Search by Date (MM/DD/YY)")
        print("3) Search by Sender Address")
        choice = input("Select search type: ")

        search_term = input("Enter search term: ")

        try:
            pop_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pop_conn.connect((self.server_ip, POP3_PORT))
            pop_conn.recv(1024)
            pop_conn.sendall(f"USER {self.username}\r\n".encode())
            pop_conn.recv(1024)
            pop_conn.sendall(f"PASS {self.password}\r\n".encode())
            pop_conn.recv(1024)

            pop_conn.sendall("LIST\r\n".encode())
            response = pop_conn.recv(4096).decode()

            emails = response.split("\n")[1:-2]  # Ignore first and last response line
            matching_emails = []

            for email_info in emails:
                email_num = email_info.split()[0]
                pop_conn.sendall(f"RETR {email_num}\r\n".encode())
                email_content = pop_conn.recv(4096).decode()
                if search_term in email_content:
                    matching_emails.append(email_content)

            if matching_emails:
                print("\nMatching Emails:\n")
                for email in matching_emails:
                    print(email, "\n" + "-" * 50)
            else:
                print("No matching emails found.")

            pop_conn.sendall("QUIT\r\n".encode())
            pop_conn.close()
        except Exception as e:
            print(f"Error while searching emails: {e}")

if __name__ == "__main__":
    server_ip = input("Enter the MailServer IP address: ")
    client = MailClient(server_ip)
    client.start()

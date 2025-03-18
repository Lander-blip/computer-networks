import socket
import getpass
import datetime
import argparse

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
        # Remove all "" characters before sending
        message = message.replace("", "")
        self.smtp_socket.sendall(message.encode())

    def _receiveSMTP(self):
        response = self.smtp_socket.recv(1024).decode()
        return response

    # --------------------------
    # POP3 helper methods
    # --------------------------
    def _sendPOP(self, message):
        # Remove all "" characters before sending
        message = message.replace("", "")
        self.pop3_socket.sendall(message.encode())

    def _receivePOP(self, multiline=False):
        if not multiline:
            response = self.pop3_socket.recv(1024).decode()
            return response
        else:
            # Read lines until termination sequence is detected
            lines = []
            while True:
                chunk = self.pop3_socket.recv(1024).decode()
                lines.append(chunk)
                if "\n.\n" in chunk or chunk.strip() == ".":
                    break
            return "".join(lines)

    # --------------------------
    # Sending Email (SMTP)
    # --------------------------
    def send_email(self):
        # SMTP interaction
        #self._receiveSMTP()  # Read server greeting

        # Send HELO command
        
        self._sendSMTP("HELO " + self.server_ip + "\n")
        self._receiveSMTP()

        # Send MAIL FROM command
        response = "501"
        while "501" in response:
            mail_from = input("From: ")
            self._sendSMTP(f"MAIL FROM: <{mail_from}>\n")
            response = self._receiveSMTP()

        # Send RCPT TO command (repeat until no error)
        response = "550"
        while "550" in response:
            to_address = input("To: ")
            self._sendSMTP(f"RCPT TO: <{to_address}>\n")
            response = self._receiveSMTP()

        # Send DATA command
        self._sendSMTP("DATA\n")
        self._receiveSMTP()

        # Send email headers and body
        subject = "Subject: " + input("Subject: ") + "\n"
        timestamp = datetime.datetime.now().strftime("%m/%d/%Y : %H : %M")
        received_line = f"Received: {timestamp}\n"
        self._sendSMTP(subject)
        self._sendSMTP(received_line)
        print("Enter message body, end with a line containing only '.':")
        while True:
            line = input() + "\n"
            self._sendSMTP(line)
            if line == ".\n":
                print("EMAIL COMPLETE")
                break

        # End DATA with termination sequence
        # self._sendSMTP("\n.\n")
        # self._receiveSMTP()

        # Optionally, send QUIT (or keep connection open for further emails)
        # self._sendSMTP("QUIT\n")
        # self._receiveSMTP()

    # --------------------------
    # Managing Emails (POP3)
    # --------------------------
    def manage_emails(self):
        # Connect to POP3 server
        self.connectPOP()
        greeting = self._receivePOP()
        print("POP3 Server:", greeting.strip())

        # Prompt for POP3 credentials (separate from SMTP)
        authenticated = False
        while not authenticated:
            pop_username = input("Enter your POP3 username: ")
            pop_password = getpass.getpass("Enter your POP3 password: ")
            self._sendPOP(f"USER {pop_username}\n")
            user_resp = self._receivePOP()
            if not user_resp.startswith("+OK"):
                print("USER command rejected. Try again.")
                continue
            self._sendPOP(f"PASS {pop_password}\n")
            pass_resp = self._receivePOP()
            if pass_resp.startswith("+OK"):
                authenticated = True
                print("Authentication successful.")
            else:
                print("Authentication failed. Please try again.")

        # Retrieve and display email summary using LIST
        self._sendPOP("LIST\n")
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
            self._sendPOP(command + "\n")
            if command.upper().startswith("RETR"):
                resp = self._receivePOP(multiline=True)
            else:
                resp = self._receivePOP()
            print(resp.strip())
            if command.upper() == "QUIT":
                break

        self.pop3_socket.close()

    # --------------------------
    # Searching Emails (POP3)
    # --------------------------
    def search_emails(self):
        # Connect to POP3 server
        self.connectPOP()
        greeting = self._receivePOP()
        print("POP3 Server:", greeting.strip())

        # Prompt for POP3 credentials (reuse same method as manage_emails)
        authenticated = False
        while not authenticated:
            pop_username = input("Enter your POP3 username: ")
            pop_password = getpass.getpass("Enter your POP3 password: ")
            self._sendPOP(f"USER {pop_username}\n")
            user_resp = self._receivePOP()
            if not user_resp.startswith("+OK"):
                print("USER command rejected. Try again.")
                continue
            self._sendPOP(f"PASS {pop_password}\n")
            pass_resp = self._receivePOP()
            if pass_resp.startswith("+OK"):
                authenticated = True
                print("Authentication successful.")
            else:
                print("Authentication failed. Please try again.")

        # Get a list of message numbers using LIST
        self._sendPOP("LIST\n")
        list_response = self._receivePOP(multiline=True)
        # Parse the LIST response into message numbers
        # Expected format:
        # +OK N messages
        # 1. sender time subject
        # 2. sender time subject
        # .
        lines = list_response.splitlines()
        message_nums = []
        for line in lines:
            # Skip the initial +OK and the terminating dot
            if line.startswith("+OK") or line.strip() == ".":
                continue
            # Assume each line starts with a number followed by a dot
            parts = line.split('.', 1)
            if parts and parts[0].isdigit():
                message_nums.append(int(parts[0]))
        if not message_nums:
            print("No messages to search.")
            self._sendPOP("QUIT\n")
            self._receivePOP()
            self.pop3_socket.close()
            return

        # Present search options
        print("\nSearch Options:")
        print("1) Search by words/sentences")
        print("2) Search by time (format MM/DD/YYYY)")
        print("3) Search by sender address")
        option = input("Select search option (1/2/3): ").strip()

        criteria = input("Enter search term: ").strip().lower()

        # For each message number, retrieve the full message and check if it matches the criteria.
        found_messages = []
        for num in message_nums:
            self._sendPOP(f"RETR {num}\n")
            msg_response = self._receivePOP(multiline=True)
            # Remove POP3 protocol response lines for searching.
            msg_lines = msg_response.splitlines()
            # Filter out the status and termination lines.
            content_lines = [line for line in msg_lines if not line.startswith("+OK") and line.strip() != "."]
            content = "\n".join(content_lines)
            content_lower = content.lower()
            if option == "1":
                # Search the entire content for the term.
                if criteria in content_lower:
                    found_messages.append((num, content))
            elif option == "2":
                # Look for the Received: header. The date is expected to be in MM/DD/YYYY format.
                for line in content_lines:
                    if line.lower().startswith("received:"):
                        # Extract the date portion.
                        # For example: "Received: 03/18/2025 : 10 : 59"
                        header = line[len("Received:"):].strip()
                        # Split by ":"; the first token should be the date.
                        tokens = header.split()
                        if tokens:
                            date_str = tokens[0]
                            if criteria == date_str:
                                found_messages.append((num, content))
                        break
            elif option == "3":
                # Look for the From: header.
                for line in content_lines:
                    if line.lower().startswith("from:"):
                        header = line[len("From:"):].strip().lower()
                        if criteria in header:
                            found_messages.append((num, content))
                        break
            else:
                print("Invalid search option.")
                break

        if found_messages:
            print("\nSearch Results:")
            for num, msg in found_messages:
                print(f"Message {num}:")
                print(msg)
                print("-" * 40)
        else:
            print("No messages found matching the criteria.")

        self._sendPOP("QUIT\n")
        self._receivePOP()
        self.pop3_socket.close()

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
    parser = argparse.ArgumentParser(description="The adress of the SMPTY and POP3 server")
    parser.add_argument('adress', type=str, help='A string as adress')
    args = parser.parse_args()
    server_ip = args.adress
    client = MailClient(server_ip)
    client.start()

# =======================
# Sample Input and Output
# =======================

# $ python3 mail_client.py localhost

# Output:
# Options:
# 1. Send Email
# 2. Manage Emails
# 3. Search Emails
# 4. Exit
# Choose an option: 

# -------------------
# ## SENDING MAIL ##
# -------------------

# Input:
# 1

# Output:
# From: 

# Input:
# manuel@email.com

# Output:
# To: 

# Input:
# robbe@email.com

# Output:
# Subject: 

# Input:
# Meeting Reminder

# Output:
# Enter message body, end with a line containing only '.': 

# Input:
# Hey Robbe,
# Don't forget we have a meeting scheduled for tomorrow at 10 AM.
# See you then!
# .

# Output:
# EMAIL COMPLETE

# Output:
# Options:
# 1. Send Email
# 2. Manage Emails
# 3. Search Emails
# 4. Exit
# Choose an option: 

# -------------------
# ## MANAGING MAIL ##
# -------------------

# Input:
# 2

# Output:
# POP3 Server: +OK POP3 server ready
# Enter your POP3 username: 

# Input:
# robbe

# Output:
# Enter your POP3 password: 

# Input:
# ******

# Output:
# Authentication successful.
# +OK POP3 server is ready
# Email Summary:
# +OK 3 messages
# 1. manuel@email.com 03/17/2025 : 14 : 30 Meeting Reminder
# 2. robbe@email.com 03/18/2025 : 09 : 15 Re: Meeting Reminder
# 3. liam@email.com 03/19/2025 : 16 : 45 Project Progress
# .
# Enter POP3 commands to manage your emails.
# Available commands: STAT, LIST, RETR <msg#>, DELE <msg#>, RSET, QUIT
# POP3>

# Input:
# RETR 1

# Output:
# +OK message follows
# From: manuel@email.com
# To: robbe@email.com
# Subject: Meeting Reminder
# Received: 03/17/2025 : 14 : 30
# Hey Robbe,
# Don't forget we have a meeting scheduled for tomorrow at 10 AM.
# See you then!
# .
# POP3>

# Input:
# DELE 1

# Output:
# +OK message 1 marked for deletion
# POP3>

# Input:
# RSET

# Output:
# +OK maildrop has been reset
# POP3>

# Input:
# QUIT

# Output:
# +OK POP3 server signing off

# Output:
# Options:
# 1. Send Email
# 2. Manage Emails
# 3. Search Emails
# 4. Exit
# Choose an option: 


# --------------------
# ## SEARCHING MAIL ##
# --------------------

# Input:
# 3

# Output:
# POP3 Server: +OK POP3 server ready
# Enter your POP3 username: 

# Input:
# robbe

# Output:
# Enter your POP3 password: 

# Input:
# ******

# Output:
# Authentication successful.
# +OK POP3 server is ready


# Output:
# Search Options:
# 1) Search by words/sentences
# 2) Search by time (format MM/DD/YYYY)
# 3) Search by sender address
# Select search option: 

# Input:
# 1

# Output:
# Enter search term: 

# Input:
# project

# Output:
# Search Results:
# Message 3:
# From: liam@email.com
# To: manuel@email.com
# Subject: Project Progress
# Received: 03/19/2025 : 16 : 45
# Hi Manuel,
# I made some progress on our project. Let's discuss it in the next meeting.
# Let me know when you're available!
# .

# Output:
# Options:
# 1. Send Email
# 2. Manage Emails
# 3. Search Emails
# 4. Exit
# Choose an option: 


# Input:
# 3

# Output:
# POP3 Server: +OK POP3 server ready
# Enter your POP3 username: 

# Input:
# robbe

# Output:
# Enter your POP3 password: 

# Input:
# ******

# Output:
# Authentication successful.
# +OK POP3 server is ready


# Output:
# Search Options:
# 1) Search by words/sentences
# 2) Search by time (format MM/DD/YYYY)
# 3) Search by sender address
# Select search option: 

# Input:
# 2

# Output:
# Enter search term: 

# Input:
# 03/19/2025

# Output:
# Search Results:
# Message 3:
# From: liam@email.com
# To: manuel@email.com
# Subject: Project Progress
# Received: 03/19/2025 : 16 : 45
# Hi Manuel,
# I made some progress on our project. Let's discuss it in the next meeting.
# Let me know when you're available!
# .

# Output:
# Options:
# 1. Send Email
# 2. Manage Emails
# 3. Search Emails
# 4. Exit
# Choose an option: 

# Input:
# 3

# Output:
# POP3 Server: +OK POP3 server ready
# Enter your POP3 username: 

# Input:
# robbe

# Output:
# Enter your POP3 password: 

# Input:
# ******

# Output:
# Authentication successful.
# +OK POP3 server is ready


# Output:
# Search Options:
# 1) Search by words/sentences
# 2) Search by time (format MM/DD/YYYY)
# 3) Search by sender address
# Select search option: 

# Input:
# 3

# Output:
# Enter search term: 

# Input:
# liam@email.com

# Output:
# Search Results:
# Message 3:
# From: liam@email.com
# To: manuel@email.com
# Subject: Project Progress
# Received: 03/19/2025 : 16 : 45
# Hi Manuel,
# I made some progress on our project. Let's discuss it in the next meeting.
# Let me know when you're available!
# .

# Output:
# Options:
# 1. Send Email
# 2. Manage Emails
# 3. Search Emails
# 4. Exit
# Choose an option: 

# -------------
# ## EXITING ##
# -------------

# Input:
# 4

# Output:
# Exiting.
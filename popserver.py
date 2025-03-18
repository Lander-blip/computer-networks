import argparse
import socket
import os

# ---------------------------
# Mailbox Handling (using blank lines as delimiters)
# ---------------------------
def load_mailbox(username):
    """
    Load messages for the user from 'username/my_mailbox'.
    Messages are separated by one or more empty lines.
    Returns a list of message strings.
    """
    mailbox_file = os.path.join(username, "my_mailbox")
    messages = []
    if not os.path.exists(mailbox_file):
        return messages

    with open(mailbox_file, "r") as f:
        current_message = []
        for line in f:
            # An empty (or whitespace-only) line is treated as a delimiter.
            if line.strip() == "":
                if current_message:
                    messages.append("".join(current_message).strip())
                    current_message = []
            else:
                current_message.append(line)
        if current_message:
            messages.append("".join(current_message).strip())
    return messages

def save_mailbox(username, messages):
    """
    Save the list of message strings into 'username/my_mailbox',
    separating each message with an empty line.
    """
    mailbox_file = os.path.join(username, "my_mailbox")
    with open(mailbox_file, "w") as f:
        for msg in messages:
            f.write(msg.strip() + "\n\n")  # Two newlines as separator

# ---------------------------
# User Data Handling
# ---------------------------
def load_user_data():
    """
    Load user credentials from userinfo.txt.
    Each line is in the format: <username> <password>
    Returns a dictionary mapping username to password.
    """
    users = {}
    if not os.path.exists("userinfo.txt"):
        print("ERROR: userinfo.txt not found.")
        return users
    with open("userinfo.txt", "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                username, password = parts[0], parts[1]
                users[username] = password
    return users

# ---------------------------
# Helper to Parse Message Fields
# ---------------------------
def parse_mail_fields(msg):
    """
    Parse the email message and extract the sender, received time, and subject.
    Expected lines:
      From: <sender>
      Received: <date : hour : minute>
      Subject: <subject>
    """
    sender = ""
    received = ""
    subject = ""
    for line in msg.splitlines():
        if line.startswith("From:"):
            sender = line[len("From:"):].strip()
        elif line.startswith("Received:"):
            received = line[len("Received:"):].strip()
        elif line.startswith("Subject:"):
            subject = line[len("Subject:"):].strip()
    return sender, received, subject

# ---------------------------
# POP3 Command Handlers
# ---------------------------
def handle_stat(mailbox, deletion_marks):
    """
    Return the STAT response with the number of messages (not marked for deletion)
    and total size in octets.
    """
    num = sum(1 for mark in deletion_marks if not mark)
    total_size = sum(len(msg.encode()) for i, msg in enumerate(mailbox) if not deletion_marks[i])
    return f"+OK {num} {total_size}\n"

def handle_list(mailbox, deletion_marks):
    """
    Build the LIST response displaying messages in the format:
    No. <Sender’s email id> <When received, in date : hour : minute> <Subject>
    Only messages not marked for deletion are listed.
    The response is terminated with a line containing only a dot.
    """
    lines = []
    for i, msg in enumerate(mailbox):
        if not deletion_marks[i]:
            sender, received, subject = parse_mail_fields(msg)
            lines.append(f"{i+1}. {sender} {received} {subject}")
    response = f"+OK {len(lines)} messages\n" + "\n".join(lines) + "\n.\n"
    return response

def handle_retr(mailbox, deletion_marks, msg_num):
    """
    Return the full text of the message identified by the given 1-indexed message number,
    if it exists and is not marked for deletion.
    """
    index = msg_num - 1
    if index < 0 or index >= len(mailbox) or deletion_marks[index]:
        return "-ERR no such message\n"
    msg = mailbox[index]
    return f"+OK message follows\n{msg}\n.\n"

def handle_dele(deletion_marks, msg_num):
    """
    Mark the given 1-indexed message for deletion.
    """
    index = msg_num - 1
    if index < 0 or index >= len(deletion_marks) or deletion_marks[index]:
        return "-ERR no such message\n"
    deletion_marks[index] = True
    return f"+OK message {msg_num} marked for deletion\n"

def handle_rset(deletion_marks):
    """
    Reset (unmark) all deletion marks.
    """
    for i in range(len(deletion_marks)):
        deletion_marks[i] = False
    return "+OK maildrop has been reset\n"

# ---------------------------
# Main POP3 Server Functionality
# ---------------------------
def handle_client(connection, client_address, users):
    print(f"Connection from {client_address} established.")
    try:
        # Send initial greeting.
        connection.sendall(b"+OK POP3 server ready\n")
        authenticated = False
        current_user = None
        mailbox = []
        deletion_marks = []

        while True:
            data = connection.recv(1024).decode()
            if not data:
                break
            # Filter out all  and \n characters
            data = data.replace('', '').replace('\n', '')
            print("Received command:", repr(data))
            parts = data.split()
            if not parts:
                connection.sendall(b"-ERR empty command\n")
                continue

            command = parts[0].upper()
            args = parts[1:]

            # --- Authentication Phase ---
            if not authenticated:
                if command == "USER" and args:
                    current_user = args[0]
                    connection.sendall(b"+OK User name accepted, password please\n")
                elif command == "PASS" and args and current_user:
                    password = args[0]
                    if current_user in users and users[current_user] == password:
                        authenticated = True
                        mailbox = load_mailbox(current_user)
                        deletion_marks = [False] * len(mailbox)
                        print("Authentication successful")
                        connection.sendall(b"+OK POP3 server is ready\n")
                    else:
                        connection.sendall(b"-ERR Invalid password\n")
                else:
                    connection.sendall(b"-ERR Authentication required\n")
            # --- Authenticated Commands ---
            else:
                if command == "STAT":
                    response = handle_stat(mailbox, deletion_marks)
                    connection.sendall(response.encode())
                elif command == "LIST":
                    print("LIST COMMAND")
                    response = handle_list(mailbox, deletion_marks)
                    connection.sendall(response.encode())
                elif command == "RETR":
                    if args:
                        try:
                            msg_num = int(args[0])
                            response = handle_retr(mailbox, deletion_marks, msg_num)
                            connection.sendall(response.encode())
                        except ValueError:
                            connection.sendall(b"-ERR Invalid message number\n")
                    else:
                        connection.sendall(b"-ERR RETR requires a message number\n")
                elif command == "DELE":
                    if args:
                        try:
                            msg_num = int(args[0])
                            response = handle_dele(deletion_marks, msg_num)
                            connection.sendall(response.encode())
                        except ValueError:
                            connection.sendall(b"-ERR Invalid message number\n")
                    else:
                        connection.sendall(b"-ERR DELE requires a message number\n")
                elif command == "RSET":
                    response = handle_rset(deletion_marks)
                    connection.sendall(response.encode())
                elif command == "QUIT":
                    # On QUIT, delete messages marked for deletion from mailbox and update disk.
                    new_mailbox = [msg for i, msg in enumerate(mailbox) if not deletion_marks[i]]
                    try:
                        save_mailbox(current_user, new_mailbox)
                        connection.sendall(b"+OK POP3 server signing off\n")
                    except Exception as e:
                        connection.sendall(f"-ERR {str(e)}\n".encode())
                    break
                else:
                    connection.sendall(b"-ERR Command not recognized\n")
    finally:
        connection.close()
        print(f"Connection with {client_address} closed.")

def main():
    parser = argparse.ArgumentParser(description="Start a POP3 server on a specified port")
    parser.add_argument('port', type=int, help='Port number to listen on')
    args = parser.parse_args()

    users = load_user_data()
    if not users:
        print("No user data available. Exiting.")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', args.port)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print(f"POP3 server starting on {server_address[0]} port {server_address[1]}")
    
    try:
        while True:
            connection, client_address = server_socket.accept()
            handle_client(connection, client_address, users)
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()

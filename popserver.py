import argparse
import socket
import os

# ---------------------------
# Mailbox Handling (using blank lines as delimiters)
# ---------------------------

def load_mailbox(username):
    """
    Load messages for the user from 'username/my_mailbox'.
    Each message is separated by an empty line.
    Returns a list of message strings.
    """
    mailbox_file = os.path.join(username, "my_mailbox")
    messages = []
    if not os.path.exists(mailbox_file):
        return messages

    with open(mailbox_file, "r") as f:
        current_message = []
        for line in f:
            # If the line is empty (or only whitespace), consider it as a delimiter.
            if line.strip() == "":
                if current_message:
                    # Join collected lines and append as a message.
                    messages.append("".join(current_message).strip())
                    current_message = []
            else:
                current_message.append(line)
        if current_message:
            messages.append("".join(current_message).strip())
    return messages

def save_mailbox(username, messages):
    """
    Save the given list of message strings into 'username/my_mailbox',
    using an empty line as a delimiter between messages.
    """
    mailbox_file = os.path.join(username, "my_mailbox")
    with open(mailbox_file, "w") as f:
        for msg in messages:
            f.write(msg.strip() + "\n\n")  # Two newlines to separate messages

# ---------------------------
# User Data Handling
# ---------------------------

def load_user_data():
    """
    Load user credentials from userinfo.txt.
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
# POP3 Command Handlers
# ---------------------------

def handle_stat(mailbox, deletion_marks):
    """
    Returns the STAT response with number of messages and total size (in octets)
    of messages not marked for deletion.
    """
    num = 0
    total_size = 0
    for i, msg in enumerate(mailbox):
        if not deletion_marks[i]:
            num += 1
            total_size += len(msg.encode())
    return f"+OK {num} {total_size}\r\n"

def handle_list(mailbox, deletion_marks):
    """
    Returns the LIST response for each message that is not marked deleted.
    Message numbering is 1-indexed.
    """
    lines = []
    count = 0
    for i, msg in enumerate(mailbox):
        if not deletion_marks[i]:
            count += 1
            size = len(msg.encode())
            lines.append(f"{i+1} {size}")
    response = f"+OK {count} messages\r\n" + "\r\n".join(lines) + "\r\n"
    return response

def handle_retr(mailbox, deletion_marks, msg_num):
    """
    Returns the full message identified by msg_num (1-indexed), if it exists and is not deleted.
    """
    index = msg_num - 1
    if index < 0 or index >= len(mailbox) or deletion_marks[index]:
        return "-ERR no such message\r\n"
    msg = mailbox[index]
    # Terminate the message with a line containing only a dot.
    return f"+OK message follows\r\n{msg}\r\n.\r\n"

def handle_dele(deletion_marks, msg_num, mailbox):
    """
    Marks the given message (1-indexed) for deletion.
    """
    index = msg_num - 1
    if index < 0 or index >= len(mailbox) or deletion_marks[index]:
        return "-ERR no such message\r\n"
    deletion_marks[index] = True
    return f"+OK message {msg_num} marked for deletion\r\n"

def handle_rset(deletion_marks):
    """
    Resets (unmarks) all deletion marks.
    """
    for i in range(len(deletion_marks)):
        deletion_marks[i] = False
    return "+OK maildrop has been reset\r\n"

# ---------------------------
# Main POP3 Server Functionality
# ---------------------------

def handle_client(connection, client_address, users):
    print(f"Connection from {client_address} established.")
    try:
        # Send initial greeting
        connection.sendall(b"+OK POP3 server ready\r\n")
        authenticated = False
        current_user = None
        mailbox = []
        deletion_marks = []

        while True:
            data = connection.recv(1024).decode()
            if not data:
                break
            print("Received command:", data.strip())
            parts = data.strip().split()
            if not parts:
                connection.sendall(b"-ERR empty command\r\n")
                continue
            command = parts[0].upper()
            args = parts[1:]

            # Authentication phase
            if not authenticated:
                if command == "USER" and args:
                    current_user = args[0]
                    connection.sendall(b"+OK User name accepted, password please\r\n")
                elif command == "PASS" and args and current_user:
                    password = args[0]
                    if current_user in users and users[current_user] == password:
                        authenticated = True
                        mailbox = load_mailbox(current_user)
                        deletion_marks = [False] * len(mailbox)
                        connection.sendall(b"+OK Mailbox open, start your session\r\n")
                    else:
                        connection.sendall(b"-ERR Invalid password\r\n")
                else:
                    connection.sendall(b"-ERR Authentication required\r\n")
            else:
                # Authenticated commands
                if command == "STAT":
                    response = handle_stat(mailbox, deletion_marks)
                    connection.sendall(response.encode())
                elif command == "LIST":
                    response = handle_list(mailbox, deletion_marks)
                    connection.sendall(response.encode())
                elif command == "RETR":
                    if args:
                        try:
                            msg_num = int(args[0])
                            response = handle_retr(mailbox, deletion_marks, msg_num)
                            connection.sendall(response.encode())
                        except ValueError:
                            connection.sendall(b"-ERR Invalid message number\r\n")
                    else:
                        connection.sendall(b"-ERR RETR requires a message number\r\n")
                elif command == "DELE":
                    if args:
                        try:
                            msg_num = int(args[0])
                            response = handle_dele(deletion_marks, msg_num, mailbox)
                            connection.sendall(response.encode())
                        except ValueError:
                            connection.sendall(b"-ERR Invalid message number\r\n")
                    else:
                        connection.sendall(b"-ERR DELE requires a message number\r\n")
                elif command == "RSET":
                    response = handle_rset(deletion_marks)
                    connection.sendall(response.encode())
                elif command == "QUIT":
                    # On QUIT, remove messages marked for deletion and save mailbox
                    new_mailbox = [msg for i, msg in enumerate(mailbox) if not deletion_marks[i]]
                    save_mailbox(current_user, new_mailbox)
                    connection.sendall(b"+OK POP3 server signing off\r\n")
                    break
                else:
                    connection.sendall(b"-ERR Command not recognized\r\n")
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

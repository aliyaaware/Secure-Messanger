"""
Source Code for the server.py, CIS434 WI22
Author(s): Alex Summers, Aliya Ware
Last Edited: 3/13/22
Sources:
    Base version of the code:
    https://www.thepythoncode.com/article/make-a-chat-room-application-in-python
Notes: All uses of the open source code are marked throughout the program
"""
import socket
from threading import *
import os, signal

def send_message(message):
    """
    (str) -> None

    Sends message to each client socket in a format so the clients can read the messages
    one at a time. Also remove clients that are not connected anymore.
    """
    # make temp list for clients that are no longer connected to chat room
    temp = []
    # iterate over all connected sockets
    for client_socket in client_sockets:
        # and send the message
        try:
            # encode the message into byte form for it to be sent over the socket and send it
            client_socket.send(message.encode())
        except:
            # if client is no longer in the chat add it to temp list
            temp.append(client_socket)

    # loop through each disconnected client in temp list
    for socket_to_remove in temp:
        # remove from client socket set
        client_sockets.remove(socket_to_remove)
        # send shutdown signal to client socket
        socket_to_remove.shutdown(socket.SHUT_RDWR)
        # close connection to socket
        socket_to_remove.close()

def parse_message(message):
    """
    (str) -> [str]

    Helper function to find multiple types of messages in the socket
    """
    # initialize the list we will keep the messages in
    messages_list = []

    # find the first bracket to get the length of the message
    while (message != ""):
        start = 0
        # find the first bracket to get the length of the message
        start_bracket = message.find("|", start)
        # get length of one of the messages
        message_length = int(message[start:start_bracket])
        # append the message to the message list removing the brackets around it
        messages_list.append(message[start_bracket + 1: start_bracket + message_length - 1])
        # make the start counter to the start of the next message
        start = start_bracket + message_length
        # delete the extracted message from the string of messages
        message = message[start:]

    # return the list of messages
    return messages_list



def listen_for_client(cs):
    """
    (socket) -> None

    This function keep listening for a message from `cs` socket
    Whenever a message is received, broadcast it to all other connected clients
    """

    # loop while true
    while True:
        # try to receive message
        try:
            # keep listening for a message from `cs` socket
            msg = cs.recv(1024).decode()
        except Exception as e:
            # client no longer connected so make thread exit
            exit(1)
        else:
            # if we received a message or messages parse through
            msg_list = parse_message(msg)

        # acquire lock because modifying global var
        lock.acquire()
        # looping through each message received
        for message in msg_list:
            # print each message to show its end-to-end encrypted and server does not see
            print(message)
            # if sent a public key indicating a new user has joined the room
            if(message[0:8] == "pub_key:"):
                # if the public key is already stored meaning the user is joining the room
                if message[8:] not in public_keys:
                    # add the key to public key set
                    public_keys.add(message[8:])
                else:
                    # if user is leaving remove their key from public key set
                    public_keys.remove(message[8:])
                # format message to send to all clients
                msg = "|Keys " + " ".join(map(str, public_keys)) + "|"
                # add length of message to the message so clients can parse through multiple
                msg = str(len(msg)) + msg
            # send the list of public keys to all the clients
            send_message(msg)

        # if client this thread is servicing is no ling in chat
        if (cs not in client_sockets):
            # release lock because we are not accessing global variable anymore
            lock.release()
            # break through loop so the thread can terminate
            break
        # release lock because we are not accessing global variable anymore
        lock.release()

def user_input():
    """
    () -> None

    Function to listen to see if client wants to shut down the server and,
    if the user inputs q the server will shutdown
    """
    # loop until user quits
    while True:
        if (input().lower() == "q"):
            # print exiting message since user pressed q
            print("Exiting: q was entered by user")
            # if no one in the chat room kill the server
            os.kill(os.getpid(), signal.SIGTERM)

# initialize set that holds all the public keys
public_keys = set()
# make mutex lock for synchronization
lock = Lock()
# server's IP address and this address automaticly hosts on users network
SERVER_HOST = "0.0.0.0"

while True:
    # User inputs port/socket number of host
    SERVER_PORT = input("Please input the socket number to host on: ")
    if (SERVER_PORT == "q"):  # if user put q program terminates
        print("Exiting")  # print message for if terminating
        exit(1)  # exit program

    # this try statement is to see the user input is correct
    try:
        # strip spaces from the input
        SERVER_PORT = SERVER_PORT.strip(" ")
        # remove the new line character from the input
        SERVER_PORT = SERVER_PORT.strip("\n")
        # try to convert the port number into a string
        SERVER_PORT = int(SERVER_PORT)
        """
        -------------------------------------------------------------------------------
        OPEN SOURCE BEGINNING
        """
        # create a TCP socket
        s = socket.socket()
        # make the port as reusable port
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind the socket to the address we specified
        s.bind((SERVER_HOST, SERVER_PORT))
        # listen for upcoming connections
        s.listen(5)
        """
        OPEN SOURCE ENDING
        -------------------------------------------------------------------------------
        """
        # break out of loop since successfully set up host
        break
    except:
        # if user input incorrect print error messages
        print("ERROR: SERVER DOES NOT EXIST")
        print("Please try again")

# start the thread to listen for if the user wants to shutdown the server
t1 = Thread(target=user_input, args=())
# make the thread daemon so it ends whenever the main thread ends
t1.daemon = True
# start the thread
t1.start()


"""
-------------------------------------------------------------------------------
OPEN SOURCE BEGINNING
"""
# if successful print that the server is listening
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
# inform the user when the server will shut down
print("Note: The server will shutdown when q is pressed")
separator_token = "<SEP>" # we will use this to separate the client name & message

# initialize list/set of all connected client's sockets
client_sockets = set()

while True:
    # we keep listening for new connections all the time
    client_socket, client_address = s.accept()
    # add the new connected client to connected sockets
    client_sockets.add(client_socket)
    # start a new thread that listens for each client's messages
    t = Thread(target=listen_for_client, args=(client_socket,))
    # make the thread daemon so it ends whenever the main thread ends
    t.daemon = True
    # start the thread
    t.start()

# close client sockets
for cs in client_sockets:
    cs.close()
# close server socket
s.close()
"""
OPEN SOURCE ENDING
-------------------------------------------------------------------------------
"""




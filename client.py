"""
Source Code for the client.py, CIS434 WI22
Author(s): Alex Summers, Aliya Ware
Last Edited: 3/13/22
Sources:
    Base version of the code:
    https://www.thepythoncode.com/article/make-a-chat-room-application-in-python
Notes: All uses of the open source code are marked throughout the program
"""
import hashlib # to use the SHA-1 hash function
import random # to randomly choose a color
import socket # sockets is how clients will communicate to the server
from datetime import datetime # to timestamp each message
from threading import Thread, Lock # different thread for receiving and sending messages

import rsa # generate RSA keys
from colorama import Fore, init # color the messages
from rsa_Ecrypt import *
import os # to kill the process
import signal # to kill the process

def send_message(to_send):
    """
    (str) -> int

    Sends message to server in a format so the server can read the messages
    one at a time. returns 1 if successful 0 if not.
    """
    # Put brackets on either side of the message
    to_send = "|" + to_send + "|"

    # add the length of the message to the string
    length_of_message = len(to_send)
    to_send = str(length_of_message) + to_send

    ret = 1
    try: # send message if server is still operational
        s.send(to_send.encode())
    except: # if server closed message is not sent so return failure
        ret = 0

    return ret # return 1 if message successfully sent 0 otherwise

def parse_message(message):
    """
    (str) -> [str]

    Helper function to find multiple messages in the socket
    """
    # initialize the list we will keep the messages in
    messages_list = []

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

    # loop through each message in the message list
    for received_message in messages_list:
        # if server sent a set of keys in string form
        if (received_message[:4] == "Keys"):
            # remove the first part of the string that says "Keys" and
            temp = received_message[5:].split()

            lock.acquire() # changing public keys which is shared between threads so lock
            public_keys.clear() # clear the list of current public keys
            lock.release() # done changing public keys which is shared between threads so unlock


            key_pairs = [] # initialize key pair list variable
            # loop through keys
            for index, word in enumerate(temp):
                num = ""
                # loop through each character which is a digit
                for digit in word.strip():
                    if digit.isdigit(): # check if character is digit
                        num += digit # add digit to num
                # append key which would be n or e
                key_pairs.append(num)
                if(index%2 == 1):
                    lock.acquire() # changing public keys which is shared between threads so lock
                    public_keys.append(key_pairs) # append all current pairs
                    lock.release() # done changing public keys which is shared between threads so unlock

                    key_pairs = [] # empty key pairs list

        # check if its message that someone left
        elif(received_message[:3] == "[+]"):
            # print who left
            print(received_message)

        # if someone sent a message to this client
        elif (received_message[:5] == "Rkey:"):
            # find where the recievers key ends within the string
            Rkey_index_end = received_message.find(")") + 1
            # extract the recievers key from the string
            Rkey = (received_message[5:Rkey_index_end])[1:-1].split(", ")

            # if the recievers public key is not this clients
            if (int(Rkey[0]) != my_public_key.n or int(Rkey[1]) != my_public_key.e):
                continue # exit this if statement because the message is not for this client

            # erase the recievers key from the message
            received_message = received_message[Rkey_index_end:]

            # find the end index for the senders public key in the message
            key_end_index = received_message.find(")") + 1
            # extract the senders public key
            senders_pub_key = received_message[4:key_end_index]
            # split the pub key into a list with n as the first index e as the second
            senders_pub_key = senders_pub_key[1:-1].split(", ")

            lock.acquire() # accessing shared variable across multiple threads soon
            # if the sender public key is not in the public key
            if [senders_pub_key[0], senders_pub_key[1]] not in public_keys:
                print("ERROR: Outsider is attempting to message you") # error message
                continue # exit loop because of error
            lock.release() # not accessing shared variable across multiple threads soon

            # if senders n is larger than this clients n
            if(int(senders_pub_key[0]) > my_private_key.n):
                # decrypt with senders public key
                received_message = RSA_algorithm(received_message, int(senders_pub_key[0]), int(senders_pub_key[1]))
                # decrypt with this clients private key
                received_message = RSA_algorithm(received_message, my_private_key.n, my_private_key.d)
            else: # if senders n is smaller or equal to this clients n
                # decrypt with this clients private key
                received_message = RSA_algorithm(received_message, my_private_key.n, my_private_key.d)
                # decrypt with senders public key
                received_message = RSA_algorithm(received_message, int(senders_pub_key[0]), int(senders_pub_key[1]))

            # find the senders hash value in the message
            hash_end_index = received_message.find("]")
            # extract the senders hash value in the message
            senders_hash = received_message[key_end_index + 6:hash_end_index]


            # erase senders hash value from the message
            received_message = received_message[hash_end_index + 1:]
            # client calculates own hash value on the plain text message
            hash_object = hashlib.sha1(received_message.encode())
            # convert it to a string that is hex. form
            calculated_hash = hash_object.hexdigest()

            # this commented out line tests to see if the hash comparison between sender and reciever works
            #calculated_hash = calculated_hash[:-1]

            # if calculated hash equals senders hash value
            if calculated_hash == senders_hash:
                print(f"{received_message}\n") # message is authentic so print the message
            else: # if calculated hash does not equal senders hash value
                # print error message since the integrity has been compromised
                print(f"ERROR INTEGRITY COMPROMISED: Senders hash value does not equal the calculated.")

def listen_for_messages():
    # send public key to server can recieve all current public keys
    if(send_message(f"pub_key:{str(my_public_key)[9:]}") == 0):
        print("Chat room closed") # printing the chat room is closed if sent message unsuccessful
        return # return nothing to exit the program

    while True:
        # try to receive message
        try:
            # receive message
            message = s.recv(1024).decode()
        except: # if cannot break out of the loop to terminate program
            break

        parse_message(message) # handle the received message(s)


"""
-------------------------------------------------------------------------------
OPEN SOURCE BEGINNING
"""
# init colors
init()
# set the available colors
colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX,
    Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX,
    Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
    Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW
]

# choose a random color for the client
client_color = random.choice(colors)

# prompt the client for a name
name = input("Enter your name: ")

"""
OPEN SOURCE ENDING
-------------------------------------------------------------------------------
"""
while True:
    # User inputs server's IP address
    SERVER_HOST = input("Please input hosts IP address: ")
    if(SERVER_HOST == "q"): # if user put q program terminates
        print("Exiting") # print message for if terminating
        exit(1) # exit program

    # User inputs port/socket number of host
    SERVER_PORT = input("Please input hosts socket number: ")
    if (SERVER_PORT == "q"): # if user put q program terminates
        print("Exiting") # print message for if terminating
        exit(1) # exit program

    try:
        # remove spaces from the input
        SERVER_HOST = SERVER_HOST.strip(" ")
        # remove the new line character from the input
        SERVER_HOST = SERVER_HOST.strip("\n")

        # strip spaces from the input
        SERVER_PORT = SERVER_PORT.strip(" ")
        # remove the new line character from the input
        SERVER_PORT = SERVER_PORT.strip("\n")
        # try to convert the port number into a string
        SERVER_PORT = int(SERVER_PORT)
    except:
        # print error message
        print("ERROR: SERVER DOES NOT EXIST")
        print("Please try again")
        continue # go back to asking for IP and Port number

    """
    -------------------------------------------------------------------------------
    OPEN SOURCE BEGINNING
    """
    separator_token = "<SEP>" # we will use this to separate the client name & message

    # initialize TCP socket
    s = socket.socket()
    print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}...")
    # connect to the server
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
        break
    except:
        print("ERROR: SERVER DOES NOT EXIST")
        print("Please try again")
    """
    OPEN SOURCE ENDING
    -------------------------------------------------------------------------------
    """
# show the user they connected to host
print("[+] Connected.")

# Make list of public keys
public_keys = []
# Generate public and private key pair for client
my_public_key, my_private_key = rsa.newkeys(16)
# initialize lock for when global variables are modified or accessed
lock = Lock()
# send name to server for it to print out
send_message(f"[+] {name} connected.")
# tell them how to exit chat room
print("[+] Please input q if you want to leave the chat room at anytime")

"""
-------------------------------------------------------------------------------
OPEN SOURCE BEGINNING
"""
# make a thread that listens for messages to this client & print them
t = Thread(target=listen_for_messages)
# make the thread daemon so it ends whenever the main thread ends
t.daemon = True
# start the thread
t.start()
"""
OPEN SOURCE ENDING
-------------------------------------------------------------------------------
"""

while True:
    # input message we want to send to the server
    to_send =  input()
    # a way to exit the program
    if to_send.lower() == 'q':
        # send public key for server to remove
        send_message(f"pub_key:{str(my_public_key)[9:]}")
        # notifies everyone
        send_message(f"[+] {name} disconnected")
        # print exiting message since user pressed q
        print("Exiting: q was entered by user")
        break # break out of loop to terminate program

    """
    -------------------------------------------------------------------------------
    OPEN SOURCE BEGINNING
    """
    # add the datetime, name & the color of the sender
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    to_send = f"{client_color}[{date_now}] {name}: {to_send}{Fore.RESET}"
    """
    OPEN SOURCE ENDING
    -------------------------------------------------------------------------------
    """
    # print message in clients console
    print(f"{to_send}\n")
    # make a hash object out of the plain text message
    hash_object = hashlib.sha1(to_send.encode())
    # extract hash value out of the hash object
    hash_value = str(hash_object.hexdigest())
    # attach the hash value to the message
    to_send = f" hash[{hash_value}]{to_send}"

    # acquire lock since looping through global variable
    lock.acquire()
    # loop through each pub key
    for pub_key in public_keys:
        # extract n for RSA encryption
        n = int(pub_key[0])
        # extract e for RSA encryption
        e = int(pub_key[1])

        # the extract n and e value are not the clients n and e values
        if(n != my_public_key.n or e != my_public_key.e):
            # if this senders n is bigger than receivers n
            if(my_private_key.n > n):
                # attach receivers and senders pub key along with the message and hash value encrypted with
                # the senders private key and the receivers public
                temp = f"Rkey:{str((n,e))}key:{str(my_public_key)[9:]}{RSA_algorithm(RSA_algorithm(to_send, n, e), my_private_key.n, my_private_key.d)}"
            else:
                # attach receivers and senders pub key along with the message and hash value encrypted with
                # the senders private key and the receivers public
                temp = f"Rkey:{str((n, e))}key:{str(my_public_key)[9:]}{RSA_algorithm(RSA_algorithm(to_send, my_private_key.n, my_private_key.d), n, e)}"
            # start to send the message to the server
            if(send_message(temp) == 0):
                print("Exiting: Chat room no longer exists") # print error message for if chat room does not exist
                os.kill(os.getpid(), signal.SIGTERM) # if message not successfully sent exit program

    # done using global variables so release lock
    lock.release()

# close the socket
s.close()
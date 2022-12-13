"""
Source Code for the rsa_Encrypt.py, CIS434 WI22
Author(s): Alex Summers, Aliya Ware
Last Edited: 3/13/22
Sources: None
Notes: None
"""


def RSA_algorithm(Plain_text, n, e_or_d):
    # initialize empty string
    result = ""
    # loop through each character in the string
    for char in Plain_text:
        # convert each character to its ASCII number then apply RSA
        # and change the number back to a character and add it to result
        result += chr(((ord(char) ** e_or_d) % n))
    # return the RSA encrypted or decrypted string
    return result

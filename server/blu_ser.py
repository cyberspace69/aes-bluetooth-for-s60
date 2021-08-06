import serial, sys
import json
from base64 import *
from serial.tools import list_ports
import pyaes

# Preparing the message

'''
Below is encryption and wrapping to handle String formatting differences,
enabling compatibility of strings between Python 2 & Python 3 versions.

'''

# Message Payload formats a user input and adds it to a dictionary / payload
def message_payload(string, user='symbian-s60'):
    message = {'user': user, 'message': string.encode('utf-8')}
    payload = wrap(message)
    return payload

# Wrap turns the payload into an encrypted, base64 string
def wrap(payload):
    wrap = str(payload)
    aes = pyaes.AESModeOfOperationCTR(key.encode())
    encrypted = aes.encrypt(wrap)
    wrap = b64encode(encrypted)
    return wrap

# Unwrap turns a base64 string into decrypted JSON
def unwrap(str):
    unpacked = b64decode(str)
    aes = pyaes.AESModeOfOperationCTR(key.encode())
    unwrap = aes.decrypt(unpacked)
    unwrap = unwrap.decode('utf-8')
    unwrap = json.loads(unwrap.replace("'", '"'))
    return unwrap

'''
This is the key for the encryption / decryption.
It must equate to the same on both the client and server files.

'''

# A 256 bit (32 byte) key
key = "This_key_for_demo_purposes_only!"

'''
This discovers ports on the server and uses the one for bluetooth

'''
for com in list_ports.comports():
    # Prints available ports
    print(com)
if sys.platform.find("win") != -1:
    PORT = "/dev/cu.Bluetooth-Incoming-Port"
elif sys.platform.find("linux") != -1:
    PORT = "/dev/rfcomm0"
elif sys.platform.find("darwin") != -1:
    PORT = "/dev/tty.pybook"
else:
    PORT = "/dev/cu.Bluetooth-Incoming-Port"

serial = serial.Serial(PORT)

print("Waiting for message...")

'''
While the connection is active..
'''
while True:
    # Reads the message received over the bluetooth port
    msg = serial.readline().strip()
    # Unwraps the encrypted message
    decrypted = unwrap(msg)
    # Prints the decrypted message
    print(decrypted)
    # Dictionary message to send values back to the device
    dict_ciph = {"key_1": "value", "key_2": "value2"}
    # Wraps / encrypts the message
    pack_response = wrap(dict_ciph)
    # Prints the encrypted message back
    print(pack_response)
    # Adds a trailing "\r" to the message
    response = pack_response + b"\r"
    # Transmits the encrypted message over the bluetooth
    serial.write(response)

    break
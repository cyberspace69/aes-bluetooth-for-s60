import pyaes
import appuifw, e32
from base64 import *
from s60_simplejson import simplejson
import btsocketplus as socket

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
    unwrap = simplejson().loads(unwrap.replace("'", '"'))
    return unwrap

ECHO = True
def choose_service(services):
    names = []
    channels = []
    for name, channel in services.items():
        names.append(name)
        channels.append(channel)
    index = appuifw.popup_menu(names, u"Choose service")
    return channels[index]

'''
Read and Echo handles the bluetooth sending / receiving.

'''

def read_and_echo(fd, key):
    buf = r = ""
    message = ""
    while r != "\n" and r != "\r":
        r = fd.read(1)
        if ECHO: fd.write(r)
        buf += r
        message += r
    if ECHO:fd.write("\n")
    decrypted = unwrap(message[:-1])
    return decrypted

address, services = socket.bt_discover()
channel = choose_service(services)
conn = socket.socket(socket.AF_BT, socket.SOCK_STREAM)
conn.connect((address, channel))
to_peer = conn.makefile("rw", 0)

'''
This is the key for the encryption / decryption.
It must equate to the same on both the client and server files.

'''

# A 256 bit (32 byte) key
key = "This_key_for_demo_purposes_only!"

# This initializes simplejson for JSON parsing
s = simplejson()

'''
While the connection is active..
'''
while True:
    # Starts a pop up to ask for user input
    msg = appuifw.query(u"Send a message", "text")
    # Converts the message into an encrypted string
    message = message_payload(msg)
    # Sends the encrypted message to the server, note the trailing "\r"
    print >> to_peer, message + "\r"
    # Prints the base64 string of the message on the device
    print "Sending: " + repr(message)
    print "Waiting for reply..."
    # Handles the receiving and decryption of response from the server
    reply = read_and_echo(to_peer, key)
    print "now printing the reply.."
    # Prints the decrypted response on the device
    print repr(reply)
    # Executes a pop up notifying completion
    appuifw.note(unicode("finished"), "info")
    break

# Closes the socket and connection to the server
to_peer.close()
conn.close()
print "bye!"

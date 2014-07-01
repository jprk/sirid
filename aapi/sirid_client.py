#!/usr/bin/python

import socket
import sys
import codecs

HOST, PORT = "localhost", 9999
xmlblob = codecs.open ( sys.argv[1], 'r', 'utf-8' )
datalist = xmlblob.readlines()
data = ''.join(datalist)
xmlblob.close()

do_receive_loop = False
if "get_long_status" in data:
    do_receive_loop = True
print type(data)

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow reusing ports
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    # Connect to server and send data
    print "connecting"
    sock.connect((HOST, PORT))
    print "sending data"
    sock.sendall(data.encode('utf-8') + "\n")

    # Receive data from the server and shut down
    if do_receive_loop :
        print "waiting for response"
        while True:
            received = sock.recv(1024)
            print received
finally:
    print "closing socket ..."
    sock.close()

print "Sent:     {0}".format(data.encode('utf-8'))
#print "Received: {0}".format(received)

#!/usr/bin/python

import socket
import select
import sys
import codecs

HOST, PORT = "localhost", 9999
# HOST, PORT = "192.168.254.222", 9999
xmlblob = codecs.open ( sys.argv[1], 'r', 'utf-8' )
datalist = xmlblob.readlines()
data = ''.join(datalist)
xmlblob.close()

do_receive_loop = False
if "get_long_status" in data:
    do_receive_loop = True
print type(data)

print "terminal encoding:", sys.stdout.encoding

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
    print "sent: " + data.encode('utf-8')

    # Receive data from the server and shut down
    if do_receive_loop :
        print "waiting for response"
        sock.setblocking(0)
        while True:
            ready = select.select([sock],[],[],5)
            if ready[0]:
                received = sock.recv(1024)
                sys.stdout.write(received)
                if "simulation_finished" in received:
                    break
except socket.error as e:
    print "socket.error %d: %s" % (e.errno, e.strerror.decode('cp1250'))
finally:
    print
    print "closing socket ..."
    sock.close()

#print "Received: {0}".format(received)

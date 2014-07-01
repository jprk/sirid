#
# SIRID socket interface for Aimsun simulator
#
# Originally this should have been implemented using ZMQ, but due to
# problems in getting ZMQ compiled and running in the bundled Python 2.6.2
# interpreter of Aimsun 7 and 8 we resorted to writig our own interface
import socket
import Queue
import logging
from AAPI import AKIPrintString
import pickle
import threading

logger = logging.getLogger('aapi_gantry.interface')

# Constants
LANE_CLOSURE = 1
SPEED_LIMIT  = 2
VMS_TEXT     = 3

class NoData(Exception) :
    def __init__ ( self ) :
        pass
    def __str__ ( self ) :
        return 'NoData'

class GantryInterface :

    def __init__ ( self ) :
        self._qin  = Queue.Queue()
        self._qout = Queue.Queue()
        self._socket = None

    def set_socket(self, sirid_socket):
        self._socket = sirid_socket

    def get_command ( self ) :
        logger.debug("get_command()")
        try :
            return self._qin.get_nowait()
        except Queue.Empty as e :
            raise NoData() 

    def put_command(self, command):
        logger.debug("put_command()")
        self._qin.put_nowait(command)

    def put_measurements(self, measurements):
        logger.debug("put_measurements()")
        self._qout.put_nowait(measurements)
        if self._socket:
            while not self._qout.empty():
                measurements = self._qout.get_nowait()
                data = pickle.dumps(measurements, -1)
                msg_str = "%05d" % len(data)
                if len(msg_str) != 5:
                    logger.debug("EXCEPTION: msg_str=`%s`", msg_str)
                    raise ValueError("Message length should be represented by five characters")
                logger.debug("sending message length as `%s`" % msg_str)
                self._socket.sendall(msg_str)
                logger.debug("sending measurements")
                self._socket.sendall(data)
                logger.debug("sent measurements")

    def start_receiving(self):
        logger.debug("creating thread")
        self._server = threading.Thread(target=gantry_socket_thread,args=(self,))
        logger.debug("starting interface thread")
        self._server.start()
        logger.debug("interface thread started")

def gantry_socket_thread(interface):
    tlogger = logging.getLogger('aapi_gantry.interface.thread')
    tlogger.debug("started gantry_socket_thread(%s)" % repr(interface))
    t = threading.current_thread()
    AKIPrintString("%s: gantry_socket_server thread started" % t.name)
    # Send response to the sirid server process that we are up and running
    sirid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sirid_socket.connect(('localhost', 1251))
    sirid_socket.sendall('AIMSUN_UP_AND_RUNNING')
    AKIPrintString("%s: sent message to sirid server" % t.name)
    tlogger.debug("sent AIMSUN_UP_AND_RUNNING")

    interface.set_socket(sirid_socket)

    # Now enter the loop processing commands
    while True:
        data = sirid_socket.recv(1024)
        if data == '@LOCK':
            AKIPrintString("%s: locking other threads" % t.name)
            #GLOBALS.lock.acquire()
            AKIPrintString("%s: locked other threads" % t.name)
        elif data == '@UNLOCK':
            AKIPrintString("%s: unlocking other threads" % t.name)
            #GLOBALS.lock.release()
            AKIPrintString("%s: unlocked other threads" % t.name)
        elif data == '@EXIT':
            AKIPrintString("%s: exit requested" % t.name)
        else:
            AKIPrintString("%s: Received data `%s`" % (t.name, repr(data)))
            tlogger.debug("received data")
            command_item = pickle.loads(data)
            tlogger.debug("putting into queue")
            interface.put_command(command_item)
            tlogger.debug("put into queue")
            AKIPrintString("%s: Command item `%s` put into queue" % (t.name, repr(command_item)))

        AKIPrintString("%s: looping back to next recv()" % t.name)

    AKIPrintString("%s: clsing socket" % t.name)
    sirid_socket.close()
    # Create the server, binding to localhost on port 9999
    #server = SocketServer.TCPServer((HOST, PORT), GantryRequest)
    #server.timeout = 30
    #AKIPrintString("%s: handle_request()" % t.name)
    #server.handle_request()
    AKIPrintString("%s: exitting" % t.name)

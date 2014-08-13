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
import packet

logger = logging.getLogger('aapi_gantry.interface')

# Constants
LANE_CLOSURE = 1
SPEED_LIMIT  = 2
VMS_TEXT     = 3

# Lock object that is used for synchronisation
LOCK = threading.Lock()

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
        self._is_synchronous = True

    def set_socket(self, sirid_socket):
        self._socket = sirid_socket

    def get_command ( self ) :
        logger.debug("get_command()")
        try :
            return self._qin.get_nowait()
        except Queue.Empty as e :
            raise NoData() 

    def put_command(self, command):
        logger.debug("put_command(%s)" % repr(command))
        self._qin.put_nowait(command)

    def put_measurements(self, measurements):
        """Store measurements from detectors in a queue and send them to server as soon as the
        communication has been established."""
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

    def is_synchronous(self):
        return self._is_synchronous

    def wait_on_control_action(self):
        if self._is_synchronous:
            AKIPrintString("wait_on_control_action(): acquiring lock")
            logger.debug("wait_on_control_action(): acquiring lock")
            LOCK.acquire()
            logger.debug("wait_on_control_action(): lock acquired")
            AKIPrintString("wait_on_control_action(): lock acquired")

    def start_receiving(self):
        logger.debug("creating thread")
        self._server = threading.Thread(target=gantry_socket_thread,args=(self,))
        logger.debug("starting interface thread")
        self._server.start()
        logger.debug("interface thread started")


def gantry_socket_thread(interface):
    """Communication thread for the SIRID gantry interface,.


    :type interface: GantryInterface
    :param interface:
    """

    tlogger = logging.getLogger('aapi_gantry.interface.thread')
    tlogger.debug("started gantry_socket_thread(%s)" % repr(interface))

    if interface.is_synchronous():
        # For the synchronous operation mode we have to lock the execution of Aimsun after sending detector data
        if LOCK.locked():
            tlogger.warning("synchronous interface but lock has been acquired already - synchronisation problems?")
        else:
            logger.debug("acquiring the Aimsun lock for the first time")
            LOCK.acquire()
            logger.debug("Aimsun lock acquired")


    t = threading.current_thread()
    AKIPrintString("%s: gantry_socket_server thread started" % t.name)
    # Send response to the SIRID server process that we are up and running
    sirid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sirid_socket.connect(('localhost', 1251))
    sirid_socket.sendall('AIMSUN_UP_AND_RUNNING')
    AKIPrintString("%s: sent message to sirid server" % t.name)
    tlogger.debug("sent AIMSUN_UP_AND_RUNNING, waiting on configuration data")

    interface.set_socket(sirid_socket)

    # Now enter the loop processing commands
    while True:

        if data == '@LOCK':
            AKIPrintString("%s: locking other threads" % t.name)
            #GLOBALS.lock.acquire()
            AKIPrintString("%s: locked other threads" % t.name)
        elif data == '@UNLOCK':
            AKIPrintString("%s: unlocking other threads" % t.name)
            tlogger.debug("command: UNLOCK")
            if interface.is_synchronous():
                # Receiving a message means receiving a command and we shall therefore unlock the AAPI thread.
                if LOCK.locked():
                    logger.debug("releasing lock")
                    LOCK.release()
                    logger.debug("lock released")
                else:
                    tlogger.warning("synchronous interface but lock has not been locked - synchronisation problems?")
            else:
                tlogger.warning("@UNLOCK command is ignored in asynchronous operation mode")
            AKIPrintString("%s: unlocked other threads" % t.name)
        elif data == '@EXIT':
            AKIPrintString("%s: exit requested" % t.name)
        else:
            AKIPrintString("%s: received data `%s`" % (t.name, repr(data)))
            tlogger.debug("received data %s" % repr(data))
            command_item = pickle.loads(data)
            tlogger.debug("putting into queue")
            interface.put_command(command_item)
            tlogger.debug("put command %s into queue" % repr(command_item))
            AKIPrintString("%s: Command item `%s` put into queue" % (t.name, repr(command_item)))

        AKIPrintString("%s: looping back to next recv()" % t.name)

    AKIPrintString("%s: closing socket" % t.name)
    tlogger.debug("closing socket")
    sirid_socket.close()
    # Create the server, binding to localhost on port 9999
    #server = SocketServer.TCPServer((HOST, PORT), GantryRequest)
    #server.timeout = 30
    #AKIPrintString("%s: handle_request()" % t.name)
    #server.handle_request()
    AKIPrintString("%s: exitting" % t.name)

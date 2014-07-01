#!/usr/bin/python
from collections import defaultdict
import threading
import socket
import SocketServer
import sys
import xml.etree.ElementTree as Et
from xml.parsers.expat import ExpatError
import _winreg as wreg
import os
import pickle

# @type boolean
AIMSUN_RUNNING = False
# @type socket
AIMSUN_LISTEN_SOCKET = None
# @type socket
AIMSUN_DATA_SOCKET = None
# @type int
AIMSUN_PORT = 1251
# @type str
LAST_MEASUREMENTS = Et.tostring(Et.Element('root'),'UTF-8')
# @type Thread
RECEIVER_LOCK = threading.Lock()
#
REQUEST_WFILE = None

def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)

def aimsun_receiver():
    global LAST_MEASUREMENTS
    global AIMSUN_DATA_SOCKET
    data_recv = None
    while True:
        # First portion is the length as 5 digit integer
        head_len = 0
        data = ''
        while head_len < 5:
            data_recv = AIMSUN_DATA_SOCKET.recv(5-head_len)
            if not data_recv:
                break
            data += data_recv
            head_len += len(data_recv)
        # We have to break the outer loop as well
        if not data_recv:
            break
        # Convert string to integer representing message length in bytes
        msg_len = int(data)
        # Announce message length
        print "Aimsun sent %s bytes" % msg_len
        # Now fetch the whole string of msg_len
        data = ''
        data_len = 0
        while data_len < msg_len:
            data_recv = AIMSUN_DATA_SOCKET.recv(min(msg_len-data_len,8192))
            if not data_recv:
                break
            data += data_recv
            data_len += len(data_recv)
        # We have to break the outer loop as well
        if not data_recv:
            break
        # Announce that the message has been read
        print 'Got the whole message'
        time_str, dets = pickle.loads(data)

        # Convert measurement data to XML
        gantry = recursive_defaultdict()
        for det in dets:
            # Consult aapi_gantry.py to see how these pieces are glued together
            det_name, det_map, data = det
            id_gantry, id_device, id_sub_device, id_lane, str_lane = det_map
            gantry[id_gantry][id_device][id_sub_device] = (det_name, id_lane, str_lane, data)

        # Create root element
        root = Et.Element('root')
        for id_gantry in gantry:
            print id_gantry
            gantry_node = Et.SubElement(root, 'gantry', attrib={'id': str(id_gantry)})
            devices = gantry[id_gantry]
            for id_device in devices:
                device_node = Et.SubElement(gantry_node, 'device', attrib={'id': str(id_device)})
                sub_devices = devices[id_device]
                for id_sub_device in sub_devices:
                    det_name, id_lane, str_lane, data = sub_devices[id_sub_device]
                    #
                    sub_device_node = Et.SubElement(device_node,
                                                    'subdevice',
                                                    attrib={'id': str(id_sub_device), 'time_stamp': time_str})
                    lane_node = Et.SubElement(sub_device_node,
                                              'lane',
                                              attrib={'id': str(id_lane), 'lane': str_lane})
                    print "   %d/%d (%s)" % (id_device, id_sub_device, det_name)
                    count, speed, occup = data
                    for i in xrange(9):
                        category_node = Et.SubElement(lane_node, 'lane', attrib={'id': str(i)})
                        count_node = Et.SubElement(category_node, 'intensity')
                        speed_node = Et.SubElement(category_node, 'speed')
                        occup_node = Et.SubElement(category_node, 'occupancy')
                        count_node.text = str(count[i])
                        speed_node.text = str(speed[i])
                        occup_node.text = str(occup[i])
                        print "    [%d]: %10f %10f %10f" % (i, count[i], speed[i], occup[i])

        # Convert it to global string variable. Yuck.
        # The global is needed due to possible "GET_LONG_STATUS" request from the client.
        LAST_MEASUREMENTS = Et.tostring(root, 'UTF-8')
        send_last_measurements()

    print 'Aimsun disconnected, receiver thread finished'


def send_last_measurements():
    print 'send_last_measurement begin'
    with RECEIVER_LOCK:
        REQUEST_WFILE.write(LAST_MEASUREMENTS)
        REQUEST_WFILE.flush()
    print 'send_last_measurement end'

def start_aimsun():
    global AIMSUN_DATA_SOCKET
    # Connect to the windows registry and find out the location of Aimsun executable
    rh = wreg.ConnectRegistry(None, wreg.HKEY_LOCAL_MACHINE)
    kh = wreg.OpenKey(rh, r"SOFTWARE\TSS-Transport Simulation Systems\Aimsun\7.0.0")
    home_dir, val_type = wreg.QueryValueEx(kh, "HomeDir")
    print "Aimsun is located in `%s`" % home_dir
    aimsun_exe = "Aimsun.exe"
    aimsun_path = os.path.join(home_dir, aimsun_exe)
    # This starts Aimsun as a seaprate process and waits for it os become ready
    pid = os.spawnl(os.P_NOWAIT, aimsun_path, aimsun_exe, "-script", "aimsun_init_replication_v7.py",
                    "sokp.ang", "31334", "aapi_gantry.py")
    print "Aimsun started as process %d, waiting for ping" % pid
    AIMSUN_LISTEN_SOCKET.listen(1)
    # Now we have it up an running
    AIMSUN_DATA_SOCKET, addr = AIMSUN_LISTEN_SOCKET.accept()
    print "Something connected from", addr
    # Give Aimsun one minute to start
    AIMSUN_DATA_SOCKET.settimeout(60)
    data = AIMSUN_DATA_SOCKET.recv(1024)
    # Make the socket blocking
    AIMSUN_DATA_SOCKET.settimeout(None)
    print "Data:",data
    # Start receiver thread
    RECEIVER_THREAD = threading.Thread(target=aimsun_receiver)
    RECEIVER_THREAD.start()
    print 'Started receiver thread'
    return ( data == 'AIMSUN_UP_AND_RUNNING' )

def process_command(root):
    """Process a XML command batch sent from the controller
    :param root: Et.Element
    """

    for gantry_node in root:
        if gantry_node.tag != "gantry":
            raise ValueError('Expected <gantry> tag, got <%s>' % gantry_node.tag)
        id_gantry_server = gantry_node.attrib['id']
        for device_node in gantry_node:
            if device_node.tag != 'device':
                raise ValueError('Expected <device> tag, got <%s>' % device_node.tag)
            id_device = int(device_node.attrib['id'])
            for sub_device_node in device_node:
                if sub_device_node.tag != 'subdevice':
                    raise ValueError('Expected <subdevice> tag, got <%s>' % sub_device_node.tag)
                id_sub_device = int(sub_device_node.attrib['id'])
                if len(sub_device_node) != 1:
                    raise ValueError('Node <subdevice> has more than one child node')
                # Sub-device node contains only a single child node. This node should be a
                # command node
                command_node = sub_device_node[0]
                if command_node.tag == 'command':
                    validity = int(command_node.attrib['validity'])
                    if len(command_node) != 1:
                        raise ValueError('Node <command> has more than one child node')
                    symbol_node = command_node[0]
                    id_message = int(symbol_node.text)
                    command = (id_gantry_server, (id_device, id_sub_device, id_message, validity))
                    print "Sending command `%s` to Aimsun ..." % repr(command)
                    AIMSUN_DATA_SOCKET.sendall(pickle.dumps(command,pickle.HIGHEST_PROTOCOL))
                    print "... sent `%s`." % repr(pickle.dumps(command,pickle.HIGHEST_PROTOCOL))
                else:
                    raise ValueError('Expected <command> tag, got <%s>' % command_node.tag)

    #print "Unlocking Aimsun threads ..."
    #AIMSUN_DATA_SOCKET.sendall('@LOCK')

def process_get_long_status(root):
    """Process a XML command GET_LONG_STATUS sent from the controller
    :param root: Et.Element

    The command looks like follows:

        <?xml version="1.0" encoding="utf-8" ?>
        <gantry msg="get_long_status">
            <datetime_format>YYYY-MM-DD hh:mm:ssZ</datetime_format>
            <send_time>2011-08-13 14:12:55</send_time>
            <sender>Mogas</sender>
            <receiver>Aimsun</receiver>
            <transmission>tcp</transmission>
            <auth_code>Me be MOGAS! Me want data!</auth_code>
        </gantry>
    """

    print "get_long_status"
    send_last_measurements()
    print "get_long_status finished"

def process_xml_message(root):
    """Process a XML command batch sent from the controller
    :param root: Et.Element
    """

    #   root = tree.getroot()

    # TODO: Does not work
    #print "Locking Aimsun threads ..."
    #AIMSUN_DATA_SOCKET.sendall('@LOCK')

    # As per documentation we have two message types to receive:
    # 1) GET_LONG_STATUS encapsulated in <gantry msg="get_long_status">...</gantry>
    # 2) COMMAND encapsulated in <root><gantry id="...">...</gantry>...</root>

    if root.tag=='root':
        process_command(root)
    elif root.tag=='gantry' and root.attrib['msg']=='get_long_status':
        process_get_long_status(root)
    else:
        raise TypeError('Unsupported message type')


class GantryRequest(SocketServer.StreamRequestHandler):
    """
    The RequestHandler class for the server.

    It is instantiated once per connection to the server, and must override the
    handle() method to implement communication to the client. We make use of an
    alternative handler class that makes use of streams, which are file-like
    objects that simplify communication by providing the standard file interface.
    The server is single threaded, which means that only one client is allowed
    to connect at a time.
    """

    def handle(self):

        # Global flag indicating that we have a running instance of the microsimulator
        global AIMSUN_RUNNING
        global REQUEST_WFILE

        print "-- handler started for connection from %s" % str(self.client_address)
        REQUEST_WFILE = self.wfile
        # Infinite loop serving the requests from the SIRID hub.
        while True:
            # This will hold a parsed tree of the XML stanza
            root = None
            # This is used to accumulate the XML stanza text sent from the client
            xml_command = ""
            # Current command is not yet valid. We will wait until we have a complete and
            # valid XML stanza
            command_is_valid = False
            # Have we got a XML header already?
            have_header = False
            while not command_is_valid:
                # Each XML stanza is at least one line of text
                print "   reading one line of data"
                data = self.rfile.readline()
                # Check for terminated connection from client
                if len(data) == 0:
                    print "-- connection broken by client"
                    print '-- handler for connection %s closed' % str(self.client_address)
                    return
                # Remove leading and trailing whitespaces
                data = data.strip()
                print "   read `{0}`".format(data)
                # First line of every stanza is <?xml .... ?>
                if '<?xml' in data:
                    have_header = True
                    print "   got XML header"
                # Parse the stanza only in case it really starts with XML header
                if have_header:
                    # Append the data to xml_command
                    xml_command += data + '\n'
                    print "   read one line of XML data, feeding into parser"
                    # Feed the line to XMLParser. The content will be analysed and if `data`
                    # contains something meaningful, the parser will not raise an error
                    try:
                        root = Et.fromstring(xml_command)
                        print "   the xml_command has been parsed successfully"
                        command_is_valid = True
                    except ExpatError as e:
                        # Mention parsing error and continue to process another line of input
                        print "   ** parse error:", repr(e)
                    except:
                        print '   unexpected error:', sys.exc_info()[0]
                        print '-- handler for connection %s raising exception' % str(self.client_address)
                        raise
            # Now we have something that looks like a valid XML command stanza for a gantry server
            print '--------------------'
            print "XML COMMAND:"
            print '--------------------'
            print xml_command
            print '--------------------'
            command_is_valid = False
            have_header = False

            # Check if Aimsun is already running, if not, start it.
            if not AIMSUN_RUNNING:
                if start_aimsun():
                    AIMSUN_RUNNING = True
                    print "** Aimsun is up and running"
                else:
                    raise OSError("Cannot start Aimsun microsimulator")

            # Convert the XML command tree to a less verbose sequence of command objects for Aimsun.
            # We have a problem handling long XML messages directly in an AAPI extension due to GIL
            # (global interpreter lock) - the command is being parsed over several microsimulation
            # steps.
            process_xml_message(root)

            # Send a confirmation to the client
            # TODO: Think if this is really necessary
            #self.wfile.write("OK\n")


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 9999

    # Create a communication socket for Aimsun
    AIMSUN_LISTEN_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    AIMSUN_LISTEN_SOCKET.bind(('localhost', AIMSUN_PORT))

    # Set the socket timeout to 60 seocnds
    AIMSUN_LISTEN_SOCKET.settimeout(60)

    # Create the server, binding to localhost on port 9999
    SERVER = SocketServer.TCPServer((HOST, PORT), GantryRequest)

    #server.timeout = 10
    #server.handle_request()
    #print '-- first request handled or timeout'

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        SERVER.serve_forever()
    except:
        print 'exception occured, exitting'
        # Do not use shutdown() as this just sends message to serve_forever() which is
        # not running anymore
        # server.shutdown()
        # print 'after server.shutdown()'


#!/usr/bin/python
from collections import defaultdict
import threading
import socket
import SocketServer
import sys
import xml.etree.ElementTree as Et
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import _winreg as wreg
import os
import pickle
import gantry  # needed for CATEOGRY definition list
import re  # needed for re-formatting minidom output (only for Python <= 2.6
import packet
import logging

# @type boolean
AIMSUN_RUNNING = False
# @type socket
AIMSUN_LISTEN_SOCKET = None
# @type socket
AIMSUN_DATA_SOCKET = None
# @type int
AIMSUN_PORT = 1251
""":type : PacketCommunicator"""
AIMSUN_PACKETCOMM = None
# @type str
LAST_MEASUREMENTS = None
# @type str
SIMULATION_READY = '<?xml version="1.0" encoding="UTF-8" ?><root><gantry msg="simulation_ready"/></root>'
# @type str
SIMULATION_FINISHED = '<?xml version="1.0" encoding="UTF-8" ?><root><gantry msg="simulation_finished"/></root>'
# @type ThreadLock
RECEIVER_LOCK = threading.Lock()
# @type ThreadLock
AIMSUN_STARTUP_LOCK = threading.Lock()
#
REQUEST_WFILE = None
#
SEQUENCE_NR = 1
# See http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
MINIDOM_TEXT_RE = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)

LOGGER_NAME = "sirid_server"

stdout_logger = logging.getLogger(LOGGER_NAME)
stdout_logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# Add the handler to the logger
stdout_logger.addHandler(ch)

stdout_logger.debug("stdout logger")

def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)


def aimsun_receiver():
    global LAST_MEASUREMENTS
    global AIMSUN_PACKETCOMM
    global SEQUENCE_NR
    global AIMSUN_RUNNING

    while True:

        data = AIMSUN_PACKETCOMM.packet_receive()
        if not data:
            break

        time_str, dets = pickle.loads(data)

        # Convert measurement data to XML
        gantry_server = recursive_defaultdict()
        gs_device_type = recursive_defaultdict()
        gs_sub_device_type = recursive_defaultdict()
        for det in dets:
            # Consult aapi_gantry.py to see how these pieces are glued together
            det_name, det_map, data = det
            # TODO: This is ugly. Group the information into a class or some other structure.
            id_gantry_server, id_device, device_type, id_sub_device, \
            sub_device_type, sub_device_description, id_lane, det_type, str_lane, prefix = det_map
            # Store information needed to construct the XML output
            gs_device_type[id_gantry_server][id_device] = \
                device_type
            gs_sub_device_type[id_gantry_server][id_device][id_sub_device] = \
                (sub_device_type, sub_device_description)
            gantry_server[id_gantry_server][id_device][id_sub_device][id_lane] = \
                (det_type, det_name, prefix, str_lane, data)

        xml_string = ''
        envelope = Et.Element('root')
        for id_gantry_server in gantry_server:
            # Create root element of the gantry server packet
            root = Et.SubElement(envelope, 'gantry', attrib={'msg': 'long_status', 'id': id_gantry_server})
            print 'gantry server:', id_gantry_server
            seq_nr_node = Et.SubElement(root, 'seq_nr')
            seq_nr_node.text = str(SEQUENCE_NR)
            send_time_node = Et.SubElement(root, 'send_time')
            send_time_node.text = str(time_str)
            sender_node = Et.SubElement(root, 'sender')
            sender_node.text = id_gantry_server
            devices = gantry_server[id_gantry_server]
            for id_device in devices:
                device_type = gs_device_type[id_gantry_server][id_device]
                device_node = Et.SubElement(root, 'device', attrib={'id': str(id_device), 'type': device_type})
                sub_devices = devices[id_device]
                for id_sub_device in sub_devices:
                    sub_device_type, sub_device_description = \
                        gs_sub_device_type[id_gantry_server][id_device][id_sub_device]
                    sub_device_attribs = {'id': str(id_sub_device), 'time_stamp': time_str,
                                          'type': sub_device_type, 'description': sub_device_description}
                    sub_device_node = Et.SubElement(device_node, 'subdevice', attrib=sub_device_attribs)
                    lanes = sub_devices[id_sub_device]
                    for id_lane in lanes:
                        det_type, det_name, prefix, str_lane, data = lanes[id_lane]
                        lane_node = Et.SubElement(sub_device_node,
                                                  'lane',
                                                  attrib={'id': str(id_lane), 'type': det_type, 'lane': str_lane})
                        print "   %d/%d/%d (%s,%s)" % (id_device, id_sub_device, id_lane, det_name, prefix)
                        count, speed, occup = data
                        for i in xrange(9):
                            category_node = Et.SubElement(lane_node, 'category', attrib=gantry.CATEGORY[i])
                            count_node = Et.SubElement(category_node, 'intensity')
                            speed_node = Et.SubElement(category_node, 'speed')
                            occup_node = Et.SubElement(category_node, 'occupancy')
                            count_node.text = str(int(count[i]))
                            speed_node.text = str(float(speed[i]))
                            occup_node.text = str(float(occup[i]))
                            print "    [%d]: %10f %10f %10f" % (i, count[i], speed[i], occup[i])

        # See also http://pymotw.com/2/xml/etree/ElementTree/create.html for information about pretty-printing
        minified_str = Et.tostring(envelope, 'UTF-8')
        reparsed = minidom.parseString(minified_str)
        xml_with_text_indents = reparsed.toprettyxml(indent="  ")
        xml_string += MINIDOM_TEXT_RE.sub('>\g<1></', xml_with_text_indents)

        # Copy the result out to a global string variable. Yuck.
        # The global is needed due to possible "GET_LONG_STATUS" request from the client.
        SEQUENCE_NR += 1
        LAST_MEASUREMENTS = xml_string
        send_last_measurements()

        fhandle = open('last_measurements.xml', 'w')
        fhandle.write(LAST_MEASUREMENTS)
        fhandle.close()

    print 'Aimsun disconnected, receiver thread finished'
    AIMSUN_DATA_SOCKET = None
    AIMSUN_RUNNING = False

    print 'Notifying the controller that the simulation is no longer active'
    with RECEIVER_LOCK:
        try:
            REQUEST_WFILE.write(SIMULATION_FINISHED)
            REQUEST_WFILE.flush()
            print 'Notification sent'
        except:
            e_type, e_val, e_trace = sys.exc_info()
            print "Exception - ", e_type, e_val


def send_last_measurements():
    if LAST_MEASUREMENTS:
        print 'send_last_measurement begin'
        with RECEIVER_LOCK:
            try:
                REQUEST_WFILE.write(LAST_MEASUREMENTS)
                REQUEST_WFILE.flush()
            except:
                e_type, e_val, e_trace = sys.exc_info()
                print "Exception - ", e_type, e_val
        print 'send_last_measurement end'
    else:
        print 'no last measurements are available, ignoring this request'


def start_aimsun(is_synchronous=False):
    """Start Aimsun microsimulator.

    :type is_synchronous: bool
    :param is_synchronous:
    :return: True if Aimsun microsimulation has been started
    """
    global AIMSUN_DATA_SOCKET
    global AIMSUN_PACKETCOMM
    global RECEIVER_THREAD
    # Connect to the windows registry and find out the location of Aimsun executable
    rh = wreg.ConnectRegistry(None, wreg.HKEY_LOCAL_MACHINE)
    kh = wreg.OpenKey(rh, r"SOFTWARE\TSS-Transport Simulation Systems\Aimsun\7.0.0")
    home_dir, val_type = wreg.QueryValueEx(kh, "HomeDir")
    print "Aimsun is located in `%s`" % home_dir
    aimsun_exe = "Aimsun.exe"
    aimsun_path = os.path.join(home_dir, aimsun_exe)
    # This starts Aimsun as a separate process and waits for it to become ready
    pid = os.spawnl(os.P_NOWAIT, aimsun_path, aimsun_exe, "-script", "aimsun_init_replication_v7.py",
                    "../sokp/sokp_v7.ang", "31334", "aapi_gantry.py")
    print "** Aimsun started as process %d, waiting for ping" % pid
    try:
        AIMSUN_LISTEN_SOCKET.listen(1)
        # Now we have it up an running
        AIMSUN_DATA_SOCKET, addr = AIMSUN_LISTEN_SOCKET.accept()
        print "   Something connected from", addr
        # Give Aimsun one minute to start
        AIMSUN_DATA_SOCKET.settimeout(60)
        # Initialise Aimsun PacketCommunicator instance
        AIMSUN_PACKETCOMM = packet.PacketCommunicator(AIMSUN_DATA_SOCKET,LOGGER_NAME)
        data = AIMSUN_PACKETCOMM.packet_receive()
    except socket.timeout:
        print '!! ERROR: Timeout when waiting for Aimsun to connect'
        return False
    # Make the socket blocking
    AIMSUN_DATA_SOCKET.settimeout(None)
    print "   Data:", data
    # Check the command
    # @TODO: Move the command names to gantryinterface and import it here
    if data == packet.AIMSUN_UP:
        print "   Got the correct initial handshake, sending configuration"
        config = {'synchronous': is_synchronous}
        data = pickle.dumps(config, pickle.HIGHEST_PROTOCOL)
        AIMSUN_PACKETCOMM.packet_send(data)
        # Start receiver thread
        RECEIVER_THREAD = threading.Thread(target=aimsun_receiver)
        RECEIVER_THREAD.start()
        print '   Started receiver thread'
        # Report back to the sender
        if is_synchronous:
            REQUEST_WFILE.write(SIMULATION_READY)
            REQUEST_WFILE.flush()
        return True


def process_command(root, is_synchronous):
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
                    # TODO: This is repeated in gantryinterface.py as well
                    data = pickle.dumps(command, pickle.HIGHEST_PROTOCOL)
                    AIMSUN_PACKETCOMM.packet_send(data)
                else:
                    raise ValueError('Expected <command> tag, got <%s>' % command_node.tag)

    if is_synchronous:
        print "Unlocking Aimsun threads ..."
        AIMSUN_DATA_SOCKET.sendall('00007@UNLOCK')


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


def process_xml_message(root, is_synchronous):
    """Process a XML command batch sent from the controller
    :param root: Et.Element
    """

    # root = tree.getroot()

    # TODO: Does not work
    #print "Locking Aimsun threads ..."
    #AIMSUN_DATA_SOCKET.sendall('@LOCK')

    # As per documentation we have two message types to receive:
    # 1) GET_LONG_STATUS encapsulated in <gantry msg="get_long_status">...</gantry>
    # 2) COMMAND encapsulated in <root><gantry id="...">...</gantry>...</root>

    if root.tag == 'root':
        process_command(root, is_synchronous)
    elif root.tag == 'gantry' and root.attrib['msg'] == 'get_long_status':
        process_get_long_status(root)
    else:
        stdout_logger.error("Unsupported message " + Et.tostring(root,' UTF-8'))
        # raise TypeError('Unsupported message type')


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


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

        # Initially we assume asynchronous operation mode
        is_synchronous = False

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

            # Check that the message is of type get_long_status. In that case it may contain a child
            # element that requests our communication with the client to be synchronous.
            if root.tag == 'gantry' and root.attrib['msg'] == 'get_long_status':
                synchronous = root.find('synchronous')
                if synchronous != None:
                    is_synchronous = (synchronous.text.strip() == 'true')
                    if is_synchronous:
                        print '** Synchronous operational mode requested'
                    else:
                        print '!! Unknown text in <synchronous> tag ignored, assuming async mode'

            # Check if Aimsun is already running, if not, start it.
            with AIMSUN_STARTUP_LOCK:
                if not AIMSUN_RUNNING:
                    if start_aimsun(is_synchronous):
                        AIMSUN_RUNNING = True
                        print "** Aimsun is up and running"
                    else:
                        return
                        # raise OSError("Cannot start Aimsun microsimulator")

            # Convert the XML command tree to a less verbose sequence of command objects for Aimsun.
            # We have a problem handling long XML messages directly in an AAPI extension due to GIL
            # (global interpreter lock) - the command is being parsed over several microsimulation
            # steps.
            process_xml_message(root, is_synchronous)

            # Send a confirmation to the client
            # TODO: Think if this is really necessary
            # self.wfile.write("OK\n")

    def finish(self):
        print "-- closing connection from %s" % str(self.client_address)
        # Force close the request socket
        SocketServer.StreamRequestHandler.finish(self)
        # Force close the request socket
        self.request.shutdown(socket.SHUT_WR)
        self.request.close()


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 9999
    # HOST, PORT = "192.168.254.222", 9999

    # Check Python interpreter version. The supported version is 2.6.x
    if sys.version_info[0] != 2 or sys.version_info[1] != 6:
        print 'ERROR: This script requires Python version 2.6.x'
        sys.exit(-1)

    # Create a communication socket for Aimsun
    AIMSUN_LISTEN_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    AIMSUN_LISTEN_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    AIMSUN_LISTEN_SOCKET.bind(('localhost', AIMSUN_PORT))

    # Set the socket timeout to 60 secnds
    AIMSUN_LISTEN_SOCKET.settimeout(60)

    # Create the multithreaded version of the server, binding to localhost on port 9999
    SERVER = ThreadedTCPServer((HOST, PORT), GantryRequest)

    # server.timeout = 10
    #server.handle_request()
    print 'SIRID server component started on %s:%d, waiting for connection.' % (HOST, PORT)

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

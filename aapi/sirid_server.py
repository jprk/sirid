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
import ConfigParser
import time

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
SIMULATION_READY = '<?xml version="1.0" encoding="UTF-8" ?><root msg="simulation_ready"></root>'
# @type str
SIMULATION_FINISHED = '<?xml version="1.0" encoding="UTF-8" ?><root msg="simulation_finished"></root>'
# @type ThreadLock
RECEIVER_LOCK = threading.Lock()
# @type ThreadLock
AIMSUN_STARTUP_LOCK = threading.Lock()
#
RECEIVER_WFILES = dict()
#
RECEIVER_ADDRESS = dict()
#
SEQUENCE_NR = 1
# See http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
MINIDOM_TEXT_RE = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)

# Maximum size of a XML message. If the input buffer grows above this limit it is
# cleared and the reading starts over.
MAX_XML_SIZE = 16*1024*1024

# Buffer size. This is a chunk size
BUFFER_SIZE = 16

# Last measurements that will be sent as fake data during the first minute
LAST_MEASUREMENTS_FILE = 'last_measurements.xml'

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

file_logger = logging.getLogger(LOGGER_NAME+"_f")
file_logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.FileHandler('sirid_server.log', mode='w')
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# Add the handler to the logger
# stdout_logger.addHandler(ch)
file_logger.addHandler(ch)

stdout_logger.debug("stdout logger")
file_logger.debug("file logger")

fhandle = open(LAST_MEASUREMENTS_FILE, 'r')
LAST_MEASUREMENTS = fhandle.read()
fhandle.close()
stdout_logger.debug("last measurements loaded")

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
        envelope = Et.Element('root', attrib={'msg': 'long_status'})
        for id_gantry_server in gantry_server:
            # Create root element of the gantry server packet
            root = Et.SubElement(envelope, 'gantry', attrib={'msg': 'long_status', 'id': id_gantry_server})
            # print 'gantry server:', id_gantry_server
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
                        # print "   %d/%d/%d (%s,%s)" % (id_device, id_sub_device, id_lane, det_name, prefix)
                        count, speed, occup = data
                        for i in xrange(9):
                            category_node = Et.SubElement(lane_node, 'category', attrib=gantry.CATEGORY[i])
                            count_node = Et.SubElement(category_node, 'intensity')
                            speed_node = Et.SubElement(category_node, 'speed')
                            occup_node = Et.SubElement(category_node, 'occupancy')
                            count_node.text = str(int(count[i]))
                            speed_node.text = str(float(speed[i]))
                            occup_node.text = str(float(occup[i]))
                            # print "    [%d]: %10f %10f %10f" % (i, count[i], speed[i], occup[i])

        # See also http://pymotw.com/2/xml/etree/ElementTree/create.html for information about pretty-printing
        minified_str = Et.tostring(envelope, 'UTF-8')
        reparsed = minidom.parseString(minified_str)
        xml_with_text_indents = reparsed.toprettyxml(indent="  ")
        xml_string += MINIDOM_TEXT_RE.sub('>\g<1></', xml_with_text_indents)

        # Copy the result out to a global string variable. Yuck.
        # The global is needed due to possible "GET_LONG_STATUS" request from the client.
        SEQUENCE_NR += 1
        LAST_MEASUREMENTS = xml_string
        send_last_measurements(RECEIVER_WFILES.keys())

        fhandle = open(LAST_MEASUREMENTS_FILE, 'w')
        fhandle.write(LAST_MEASUREMENTS)
        fhandle.close()

    print '-- Aimsun disconnected, receiver thread finished'
    AIMSUN_DATA_SOCKET = None
    AIMSUN_RUNNING = False

    if RECEIVER_WFILES:
        print '-- notifying the controllers that the simulation is no longer active'
        file_logger.debug('sending notification')
        with RECEIVER_LOCK:
            print '   got lock'
            for thread_name in RECEIVER_WFILES:
                try:
                    wfile = RECEIVER_WFILES[thread_name]
                    wfile.write(SIMULATION_FINISHED)
                    wfile.flush()
                    print "   -- notification sent to receiver in", thread_name
                except:
                    e_type, e_val, e_trace = sys.exc_info()
                    print 'Exception for receiver', thread_name, '-', e_type, e_val
        print '   lock released'
    else:
        print '-- no controllers seem to be active at the moment, no notification sent'


def send_last_measurements(receiver_list):
    if LAST_MEASUREMENTS:
        # The receiver locks blocks also possible error output from the GantryRequest instance
        # If an error occurs there, it will be handled after the sending task has been completed.
        current_thread = threading.current_thread()
        master_thread_name = current_thread.name
        print '   waiting on receiver lock in master thread '+master_thread_name
        with RECEIVER_LOCK:
            file_logger.debug('locked by %s for %s' % (master_thread_name, str(receiver_list)))
            print '-- send_last_measurement begin in '+master_thread_name
            for thread_name in receiver_list:
                try:
                    wfile = RECEIVER_WFILES[thread_name]
                    print "   -- sending data to receiver %s/%s" % (thread_name, RECEIVER_ADDRESS[thread_name])
                    file_logger.debug("sending data to receiver %s/%s" % (thread_name, RECEIVER_ADDRESS[thread_name]))
                    wfile.write(LAST_MEASUREMENTS)
                    file_logger.debug("write ok")
                    wfile.flush()
                    file_logger.debug("flush ok, sent data to receiver %s/%s" % (thread_name, RECEIVER_ADDRESS[thread_name]))
                except socket.error as e:
                    file_logger.error('socket error in %s for receiver %s/%s' % (master_thread_name, thread_name, RECEIVER_ADDRESS[thread_name]))
                    print "   !! socket.error for write() in %s/%s (errno=%d, `%s`), discarding thread" % \
                          (thread_name, RECEIVER_ADDRESS[thread_name], e.errno, e.strerror)
                    RECEIVER_WFILES.pop(thread_name, None)
                except:
                    e_type, e_val, e_trace = sys.exc_info()
                    file_logger.error('exception %s (%s) in %s for receiver %s/%s' % (e_type, e_val, master_thread_name, thread_name, RECEIVER_ADDRESS[thread_name]))
                    print thread_name, "Exception -", e_type, e_val
            print '   send_last_measurement end in '+master_thread_name
        file_logger.debug('unlocked by'+master_thread_name)
        print '   lock released in '+ master_thread_name
    else:
        print '-- no last measurements are available, ignoring this request'

    stdout_logger.debug('number of active threads: %d' % threading.active_count())

def start_aimsun(is_synchronous=False, replication_id=0):
    """Start Aimsun microsimulator.

    :type replication_id: int
    :param replication_id: Aimsun object ID of the replication that shall be started.
    :type is_synchronous: bool
    :param is_synchronous: True if the synchronous operation mode has been requested.
    :return: True if Aimsun microsimulation has been started
    """
    global AIMSUN_DATA_SOCKET
    global AIMSUN_PACKETCOMM
    global AIMSUN_RECEIVER_THREAD

    # Connect to the windows registry and find out the location of Aimsun executable
    rh = wreg.ConnectRegistry(None, wreg.HKEY_LOCAL_MACHINE)
    kh = wreg.OpenKey(rh, r"SOFTWARE\TSS-Transport Simulation Systems\Aimsun\7.0.0")
    home_dir, val_type = wreg.QueryValueEx(kh, "HomeDir")
    print "Aimsun is located in `%s`" % home_dir
    aimsun_exe = "Aimsun.exe"
    aimsun_path = os.path.join(home_dir, aimsun_exe)
    # Check the replication_id
    if not replication_id: replication_id=31334
    # This starts Aimsun as a separate process and waits for it to become ready
    pid = os.spawnl(os.P_NOWAIT, aimsun_path, aimsun_exe, "-script", "aimsun_init_replication_v7.py",
                    "../sokp/sokp_v7.ang", str(replication_id), "aapi_gantry.py")
    print "** Aimsun replication %d started as process %d, waiting for ping" % (replication_id, pid)
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
        AIMSUN_RECEIVER_THREAD = threading.Thread(target=aimsun_receiver)
        AIMSUN_RECEIVER_THREAD.start()
        print '   Started receiver thread'
        # Report back to the sender
        if is_synchronous:
            print '-- sending SIMULATION_READY to the client(s)'
            for thread_name in RECEIVER_WFILES:
                wfile = RECEIVER_WFILES[thread_name]
                wfile.write(SIMULATION_READY)
                wfile.flush()
                print '   sent to %s XML %s' % (thread_name, SIMULATION_READY)
        return True


def process_command(root, is_synchronous):
    """Process a XML command batch sent from the controller
    :param root: Et.Element
    """

    is_missing_symbol = False

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
                    if len(command_node) > 2:
                        node_list = []
                        for tnode in command_node:
                            node_list.append(tnode.tag)
                        raise ValueError('Node <command> has more than two child nodes: ' + repr(node_list))
                    symbol_node = command_node.find("symbol")
                    addsymbol_node = command_node.find("addsymbol")

                    # Existing nodes evaluate to false
                    if addsymbol_node != None:
                        print "WARNING: Don't know how to handle <addsymbol>"

                    if symbol_node != None:
                        id_message = int(symbol_node.text)
                        command = (id_gantry_server, (id_device, id_sub_device, id_message, validity))
                        print "Sending command `%s` to Aimsun ..." % repr(command)
                        # TODO: This is repeated in gantryinterface.py as well
                        data = pickle.dumps(command, pickle.HIGHEST_PROTOCOL)
                        AIMSUN_PACKETCOMM.packet_send(data)
                    else:
                        print "ERROR: No <symbol> node for %s/%s/%s" % (id_gantry_server, id_device, id_sub_device)
                        print repr(symbol_node)
                        print Et.tostring(command_node)
                        is_missing_symbol = True
                else:
                    raise ValueError('Expected <command> tag, got <%s>' % command_node.tag)

    if is_missing_symbol:
        stdout_logger.error("missing <symbol> node:\n" + Et.tostring(root, 'UTF-8'))

    if is_synchronous:
        print "Unlocking Aimsun threads ..."
        AIMSUN_DATA_SOCKET.sendall('00007@UNLOCK')


def process_get_long_status(thread_name):
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

    print "-- get_long_status requested by thread %s/%s" % (thread_name, RECEIVER_ADDRESS[thread_name])
    send_last_measurements([thread_name])
    print "   get_long_status finished for thread %s/%s" % (thread_name, RECEIVER_ADDRESS[thread_name])


def process_xml_message(root, is_synchronous, thread_name):
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

    # TODO: This should be rewritten to exceptions
    log_message = True

    if root.tag == 'root':
        process_command(root, is_synchronous)
        log_message = False
    elif root.tag == 'gantry':
        if 'msg' in root.attrib:
            msg_type = root.attrib['msg']
            if msg_type == 'get_long_status':
                process_get_long_status(thread_name)
                log_message = False
            else:
                stdout_logger.error("Unsupported tag <gantry msg='%s'>" % msg_type)
        else:
            stdout_logger.error("Unsupported format of <gantry> tag: missing `msg` attribute.")
    else:
        stdout_logger.error("Unsupported root tag <%s>" % root.tag)

    if log_message:
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

    # Initially we assume asynchronous operation mode
    is_synchronous = False
    empty_count = 0

    def handle(self):

        # Global file-like object that writes to the connection to the client
        # TODO: Maybe a list of objects in case that this loop is instantiated more than once?

        current_thread = threading.current_thread()
        thread_name = current_thread.name

        # Make the information about the outbound connection global. This way also the Aimsun
        # sender thread will be able to write data to all clients
        RECEIVER_WFILES[thread_name] = self.wfile
        RECEIVER_ADDRESS[thread_name] = self.client_address

        print "-- handler %s started for connection from %s" % (thread_name, str(self.client_address))

        # Current unprocessed data read from the request
        data = ''

        # No root tag has been found
        no_root_tag = True
        start_pos = 0
        close_pos = 0
        tag_name = None
        closing_tag = None
        look_for_eet = True

        # Infinite loop serving the requests from the SIRID hub.
        while True:

            # Sanity check: limit the buffer size
            if len(data) > MAX_XML_SIZE:
                data = ''

            # Read data from the connection, maximum BUFFER_SIZE bytes
            try:
                buff = self.request.recv(BUFFER_SIZE)
            except socket.error as e:
                # The printout may interfere with printouts for receiver threads
                # with RECEIVER_LOCK:
                print "   -- socket.error in recv() for %s/%s (errno=%d, `%s`), exitting request handler" % \
                      (thread_name, self.client_address, e.errno, e.strerror)
                break

            if not buff:
                # No data from the connection means the connection has been closed
                print "   -- #%04d, empty buff [%s] after recv(), probable closed connection for %s/%s" % (empty_count, repr(buff), thread_name, str(self.client_address))
                empty_count += 1
                if empty_count >= 1000:
                    print "      too many empty buffers, quitting"
                    break
                else:
                    time.sleep(1)
                    continue

            empty_count = 0

            # Append the buffer to the existing data
            data += buff

            # This flag is set to False in case that we need to read another part of
            # the incoming message
            do_process_data = True

            # Loop over the contents of `data`
            while do_process_data:

                # Loop over the contents of `data` until an opening tag has been found or until the
                # buffer is exhausted and we shall read in the next part of the incoming message
                while no_root_tag:
                    # Find the first opening tag
                    open_pos = data.find('<', start_pos)
                    # Negative position signals that the string was not found. In such a care
                    # we will continue reading, which means first breaking out of the `no_root_tag`
                    # loop.
                    if open_pos == -1:
                        break
                    # We have the opening tag. What follows is according to the XML specification
                    # either '?xml ... >' or in case that the header is not present, the root element
                    # of the XML stanza.
                    # We need to isolate the whole element first
                    close_pos = data.find('>', open_pos)
                    if close_pos == -1:
                        # No closing mark yet, we will continue reading, which means first breaking
                        # out of the `no_root_tag` loop.
                        break
                    # We have isolated the opening element. The element tag name is either in the
                    # format of <root> or <root attr="val">. The suggested logic is therefore:
                    # look for the space, if found, the tag name is delimited by the space, otherwise
                    # it is limited by the closing mark
                    sp_pos = data.find(' ', open_pos)
                    if 0 <= sp_pos < close_pos:
                        # Tag format <root attr="val">
                        tag_name = data[open_pos+1:sp_pos]
                    else:
                        # Tag format <root>
                        tag_name = data[open_pos+1:close_pos]
                    if tag_name[0].isalpha():
                        # We have a root tag
                        print '   got root tag <%s>' % tag_name
                        no_root_tag = False
                    # In any case the further search will start after the closing tag of the identified
                    # element
                    start_pos = close_pos

                # End of the loop. In case that there is no opening tag, `no_root_tag` is still
                # True. In such a case we will interrupt the loop processing and continue to
                # reading the next part of the input message
                if no_root_tag:
                    # Do not search the already searched part of the buffer again
                    if open_pos == -1:
                        start_pos = len(data)
                    else:
                        start_pos = open_pos
                    # Signal the need to read another portion of the incoming message
                    do_process_data = False
                    continue
                # Now we continue looking for the closing counterpart of the opening tag. We will
                # start right after the closing > of the current tag, but before doing so we have
                # to verify that the root tag is not of the "empty-element" form <root ... />
                # The test for empty-element tag shall occur only in the first round of testing
                # right after the opening part of the tag has been identified.
                if look_for_eet:
                    if data[close_pos-1] == '/':
                        # Empty-element tag
                        self.process_xml_string(data[open_pos:close_pos+1])
                        # Discard the processed part of the buffer
                        data = data[close_pos+1:]
                        # And we go back to `no_root_tag`
                        no_root_tag = True
                        start_pos = 0
                        # But there might still be a payload in `data` which has not been processed,
                        # so `do_process_data` shall remain set to True
                        continue
                    else:
                        # Define what the closing tag tag is
                        closing_tag = '</'+tag_name+'>'
                        # Remember its length
                        closing_tag_len = len(closing_tag)
                        # Do not look consider empty-element tags until the next root element candidate
                        look_for_eet = False

                close_pos = data.find(closing_tag, close_pos)
                # It is not guaranteed that the current contents of `data` contains also the
                # closing tag
                if close_pos == -1:
                    # No closing tag found yet, read further on.
                    # We have to account for the possibility that a part of the closing tag has
                    # been already read (the text ends for example with '...</roo') so the
                    # position from which we continue the search is not the end of current
                    # `data` string, but it is offset by the length of the closing tag
                    close_pos = len(data)-closing_tag_len
                    if close_pos < 0:
                        close_pos = 0
                    # Signal the need to read another portion of the incoming message
                    do_process_data = False
                else:
                    # We have a closing tag
                    end_pos = close_pos+closing_tag_len
                    self.process_xml_string(data[open_pos:end_pos])
                    # Discard the part of `data` that corresponds to the XML message
                    data = data[end_pos:]
                    # Reset the state of the XML pre-parser: we have no root tag and the search
                    # start from the beginning of `data`
                    no_root_tag = True
                    start_pos = 0
                    look_for_eet = True
                    # The `data` string may still contain a part of the next XML message (or even
                    # a full one) and `do_process_data` shall therefore still remain set to True

            # End of the inner part of the `do_process_data loop

        # End of the receiver loop
        print "-- handler %s/%s returning" % (thread_name, str(self.client_address))

    def finish(self):

        current_thread = threading.current_thread()
        thread_name = current_thread.name

        print "-- closing %s connection from %s" % (thread_name, str(self.client_address))
        # Force close the request socket
        SocketServer.StreamRequestHandler.finish(self)
        # Force close the request socket
        try:
            self.request.shutdown(socket.SHUT_WR)
            self.request.close()
        except socket.error as e:
            # The printout may interfere with printouts for receiver threads
            print "   -- socket.error in finish() for %s/%s (errno=%d, `%s`) when exiting request handler" % \
                  (thread_name, self.client_address, e.errno, e.strerror)

        # Delete the entry in RECEIVER_WFILES
        RECEIVER_WFILES.pop(thread_name, None)

    def process_xml_string(self, xml_string):
        """Try to parse the string that the receiver identified as a single XML stanza."""

        # Global flag indicating that we have a running instance of the microsimulator
        global AIMSUN_RUNNING

        current_thread = threading.current_thread()
        thread_name = current_thread.name

        # Now we have something that looks like a valid XML command stanza for a gantry server
        print '--------------------'
        print "XML STRING:"
        print xml_string
        print '--------------------'

        try:
            root = Et.fromstring(xml_string)
            print "   %s: the XML string has been parsed successfully" % thread_name
        except ExpatError as e:
            # Mention parsing error and continue to process another line of input
            print "** parse error:", repr(e)
            print "   %s returning immediately" % thread_name
            return
        except:
            print '   unexpected error:', sys.exc_info()[0]
            print '-- handler %s for connection %s raising exception' % (thread_name, str(self.client_address))
            raise

        # Only one thread is allowed to start Aimsun, other threads wait until the lock has been
        # released.
        with AIMSUN_STARTUP_LOCK:
            #Check if Aimsun is already running, if not, start it.
            if not AIMSUN_RUNNING:
                # Check that the message is of type get_long_status. In that case it may contain
                # - a child element that requests our communication with the client to be synchronous,
                # - replication id to start
                replication_id = 0
                if root.tag == 'gantry' and root.attrib['msg'] == 'get_long_status':
                    synchronous = root.find('synchronous')
                    if synchronous != None:
                        # TODO: Check if self.is_synchronous is necessary. Local variable should suffice.
                        self.is_synchronous = (synchronous.text.strip() == 'true')
                        if self.is_synchronous:
                            print '** Synchronous operational mode requested'
                        else:
                            print '!! Unknown text in <synchronous> tag ignored, assuming async mode'
                    replication = root.find('replication')
                    if replication != None:
                        try:
                            replication_id= int(replication.text)
                            print '** Got replication id %s' % replication_id
                        except ValueError:
                            print '!! Unknown text in <replication> tag ignored (%s)' % replication.text
                # Start Aimsun
                if start_aimsun(self.is_synchronous, replication_id):
                    AIMSUN_RUNNING = True
                    print "** Aimsun is up and running"
                else:
                    print "!! warning: cannot start Aimsun"
                    return
                    # raise OSError("Cannot start Aimsun microsimulator")

        # Convert the XML command tree to a less verbose sequence of command objects for Aimsun.
        # We have a problem handling long XML messages directly in an AAPI extension due to GIL
        # (global interpreter lock) - the command is being parsed over several microsimulation
        # steps.
        process_xml_message(root, self.is_synchronous, thread_name)



if __name__ == "__main__":

    # host_ip_str, port_num = "127.0.0.1", 9999
    # host_ip_str, port_num = "192.168.254.222", 9999

    # Check Python interpreter version. The supported version is 2.6.x
    if sys.version_info[0] != 2 or sys.version_info[1] != 6:
        print 'ERROR: This script requires Python version 2.6.x'
        sys.exit(-1)

    # Parse the config file with host address and port number
    config = ConfigParser.RawConfigParser()
    config.read('sirid_server.ini')
    host_ip_str = config.get('local', 'host')
    port_num = config.getint('local', 'port')

    # Create a communication socket for Aimsun
    AIMSUN_LISTEN_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    AIMSUN_LISTEN_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    AIMSUN_LISTEN_SOCKET.bind(('localhost', AIMSUN_PORT))

    # Set the socket timeout to 60 secnds
    AIMSUN_LISTEN_SOCKET.settimeout(60)

    # Create the multithreaded version of the server, binding to localhost on port 9999
    SERVER = ThreadedTCPServer((host_ip_str, port_num), GantryRequest)
    SERVER.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # server.timeout = 10
    #server.handle_request()
    print 'SIRID server component started on %s:%d, waiting for connection.' % (host_ip_str, port_num)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        SERVER.serve_forever()
        print 'clean server exit'
    except KeyboardInterrupt:
        print 'keyboard interrupt, exiting'

#!/usr/bin/python
# -*- coding: windows-1250 -*-
import sys
import os
import re
from collections import defaultdict
import xml.etree.ElementTree as Et
from AAPI import *
import gantryinterface as gi
import socket
import SocketServer
import threading
import pickle
from gantry import GantryServer, GantryLoopDetector
import logging
import time

# Create a logger with name 'aapi_gantry'
logger = logging.getLogger('aapi_gantry')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('aapi_gantry.log', mode='w')
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# Add the handler to the logger
logger.addHandler(fh)

# This is just a quick hack, we shall provide for better and bulletproof
# implementation of global storage

class Globals(object):
    """Global parameters of the AAPI module"""
    detectors = []
    detection_time = 0.0
    detection_interval = 0.0
    gantry_servers = dict()
    num_vehicle_types = 0
    sections = defaultdict(list)
    vms_message_att = None
    gantry_ld_map = dict()
    time_offset = 0

SYMBOLS = dict(
    A=['Zhasnuto', 'A8 -Nebezpečí smyku', 'A15 -Práce na silnici', 'A22 -Jiné nebezpečí', 'A23 - Tvorba kolon',
       'A24 - Náledí', 'A26 – Mlha', 'A27 – Nehoda'],
    B=['Zhasnuto', '120', '100', '80', '60'],
    F=['Zhasnuto', 'Zákaz vjezdu NV', 'Šipka vlevo', 'Šipka vpravo', 'Konec omezení'],
    EA=['Zhasnuto', '500m', '1000m', '1500m', '2000m', '2500m', '3000m', '3500m', '4000m', '4500m', '5000m', '5500m',
        '6000m', '6500m', '7000m', '7500m', '8000m', '8500m', '9000m', '9500m', '10000m'],
    EF=['Zhasnuto', '3,5t', '6t', '7,5t', '9t', '12t'])

# This is the global interface module that facilitates IPC between Gantry
# server module and Aimsun
INTERFACE = gi.GantryInterface()

# Global variables are ugly, evil, but in AAPI we have no mechanism to avoid
# global storage. Pity.
GLOBALS = Globals()


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
        print "-- handler started for connection from %s" % str(self.client_address)
        # Infinite loop serving the requests from the SIRID hub.
        print "   reading a command"
        data = self.rfile.read()
        print "   putting the command into a queue"
        print data

def gantry_socket_server():
    t = threading.current_thread()
    AKIPrintString("%s: gantry_socket_server thread started" % t.name)
    # Send response to the sirid server process that we are up and running
    sirid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sirid_socket.connect(('localhost', 1251))
    sirid_socket.sendall('AIMSUN_UP_AND_RUNNING')
    AKIPrintString("%s: sent message to sirid server" % t.name)

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
            id_gantry_server, command = pickle.loads(data)
            GLOBALS.gantry_servers[id_gantry_server].process_command(command)
            AKIPrintString("%s: Received command `%s`" % (t.name, repr(command)))

        AKIPrintString("%s: looping back to next recv()" % t.name)

    AKIPrintString("%s: clsing socket" % t.name)
    sirid_socket.close()
    # Create the server, binding to localhost on port 9999
    #server = SocketServer.TCPServer((HOST, PORT), GantryRequest)
    #server.timeout = 30
    #AKIPrintString("%s: handle_request()" % t.name)
    #server.handle_request()
    AKIPrintString("%s: exitting" % t.name)

def change_vms_text(params):
    "Change the text message shown at VMS identified by `params`."
    # To set something the be displayed on a VMS is quite obscure. See
    # https://groups.yahoo.com/neo/groups/Aimsun/conversations/topics/4123
    AKIPrintString("cmd :: changing vms text " + repr(params))
    id_gantry = 'R01-R-MX10028'
    device = 3
    subdevice = 0
    msgstr = 'UNDEFINED'
    # A single VMS in Aimsun represents a gantry holding several variable message signs in reality.
    # We have to first find out to which gantry does the given VMS belong
    gantry = GLOBALS.gantry_servers[id_gantry]
    # Now update the state of the gantry object
    gantry.update_vms(device, subdevice, msgstr)
    # Fetch the complete set of messages being displayed on the gantry
    message = str(gantry)
    # Display the messages
    ANGConnSetAttributeValueStringA(GLOBALS.vms_message_att, id_gantry, AKIConvertFromAsciiString(message))

def AAPILoad():
    """


    :return:
    """
    AKIPrintString("Loading AAPI Gantry module")
    AKIPrintString("Python version: " + sys.version)
    AKIPrintString("Builtin modules: " + repr(sys.modules.keys()))
    AKIPrintString("Python executable: " + sys.executable)
    AKIPrintString("Python prefix: " + sys.prefix)
    AKIPrintString("Python exec prefix: " + sys.exec_prefix)
    AKIPrintString("Python search path: " + repr(sys.path))
    #
    AKIPrintString("Module path: " + os.path.abspath(__file__))
    mod_dir = os.path.dirname(os.path.abspath(__file__))
    #
    #AKIPrintString ( "libXML version: %d.%d.%d" % et.LIBXML_VERSION )
    #AKIPrintString ( "libXSLT version: %d.%d.%d" % et.LIBXSLT_VERSION )
    #AKIPrintString ( "lxml version: %d.%d.%d.%d" % et.LXML_VERSION )
    #
    tree = Et.parse(os.path.join(mod_dir, 'sokp.xml'))
    root = tree.getroot()
    AKIPrintString("sirid.xml root element: " + repr(root))

    GLOBALS.gantry_servers = {}
    GLOBALS.gantry_ld_map = {}
    for gantry_node in root:
        #print gantry_node.tag, gantry_node.attrib
        id_gantry = gantry_node.attrib['id']
        gantry_server = GantryServer(id_gantry)
        for device in gantry_node:
            #print ' ', device.tag, device.attrib
            id_device = int(device.attrib['id'])
            ppk = device.attrib['ppk']
            for sub_device in device:
                #print '   ', sub_device.tag, sub_device.attrib
                id_sub_device = int(sub_device.attrib['id'])
                id_type = sub_device.attrib['type']
                prefix = sub_device.attrib['prefix']
                sub_instance = gantry_server.add_sub_device(id_device, ppk, id_sub_device, id_type, prefix)
                # We need a mapping from detector id to gantry, device, subdevice
                if isinstance(sub_instance, GantryLoopDetector):
                    GLOBALS.gantry_ld_map[prefix] = (id_gantry, id_device, id_sub_device, sub_instance.id_lane, sub_instance.str_lane)
        GLOBALS.gantry_servers[id_gantry] = gantry_server
        #print gantry_server.get_gantry_messages()

    # Create the server, binding to localhost on port 9999
    #server = SocketServer.TCPServer((HOST, PORT), GantryRequest)
    #server.timeout = 10
    #AKIPrintString("handle_request()")
    #server.handle_request()
    #AKIPrintString("first request handled or timeout")
    t = threading.current_thread()
    AKIPrintString("current thread: " + t.name)

    GLOBALS.lock = threading.Lock()

    time_str = ANGConnGetScenarioTime()
    logger.debug("Scenario date and time: %s" % time_str)
    time_tuple = time.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    GLOBALS.time_offset = time.mktime(time_tuple)
    # Start a socket server
    logger.debug("AAPILoad() starting interface")
    INTERFACE.start_receiving()
    logger.debug("AAPILoad() end")
    return 0


def AAPIInit():
    """


    :return:
    """
    logger.debug("AAPIInit() begin")
    #
    #  List all sections
    #
    # Construct a regular expressions for matching the "interesting" section names
    section_re = re.compile(r"S(\d\d\d\d\d)[.]\d")
    # Get the number of sections in the model
    num_sections = AKIInfNetNbSectionsANG()
    AKIPrintString("Got %d sections:" % num_sections)
    # And loop over them to find sections with specific names
    for pos in xrange(num_sections):
        # Get internal numeric ID of the section
        id_object = AKIInfNetGetSectionANGId(pos)
        # Query the object database for a name associated with this ID
        name = ANGConnGetObjectNameA(id_object)
        # Every section behind a gantry has a name that follows the `Sdyyyy.n` format,
        # where the numeric `dyyyy` part corresponds to the numeric part of the gantry
        # name
        m = section_re.match(name)
        if m:
            # There has been a match
            gantry_id = int(m.group(1))
            # Append the internal numeric ID to a list of sections governed by that gantry
            GLOBALS.sections[gantry_id].append(id_object)
        AKIPrintString("  [%d] %d / `%s`" % (pos, id_object, name))

    #
    #  List all detectors.
    #
    # Construct a regular expressions for matching the "interesting" detector names
    detector_re = re.compile(r"LD(\d\d\d\d\d)")
    # Get the number of detectors, then for every detector get its numeric internal
    # object ID and based on the object ID get the name of the detector
    num_detectors = AKIDetGetNumberDetectors()
    AKIPrintString("Got %d detectors:" % num_detectors)
    for pos in xrange(num_detectors):
        # Get internal numeric ID of the detector
        id_object = AKIDetGetIdDetector(pos)
        # Query the object database for a name associated with this ID
        name = ANGConnGetObjectNameA(id_object)
        # Every detector used by the gantry interface has a name that follows the `LDxyyyy`
        # format, where the numeric `xyyyy` part corresponds to the numeric part of the
        # gantry name (`d` in gantry name is `x%2` - `x` is a lane ID and odd `x` values
        # correspond to `d=1`, even `x` values correspond to `d=0`)
        m = detector_re.match(name)
        if m:
            # There has been a match
            detector_name = m.group()
            # Append the internal numeric ID and detector name to a list of detectors that
            # will be reported back to the upper control level
            GLOBALS.detectors.append((id_object, detector_name))
        AKIPrintString("  [%d] %d / `%s`" % (pos, id_object, name))

    # List all vehicle types.
    # Sadly the names of vehicle types cannot be obtained in Python
    GLOBALS.num_vehicle_types = AKIVehGetNbVehTypes()
    AKIPrintString("Got %d vehicle types:" % GLOBALS.num_vehicle_types)

    # Remember the detection interval of detectors
    GLOBALS.detection_interval = AKIDetGetIntervalDetection()
    AKIPrintString("Detection interval: %fs" % GLOBALS.detection_interval)
    # Compute the first timestamp of valid detector measurement
    GLOBALS.detection_time = GLOBALS.detection_interval + AKIGetDurationTransTime()
    AKIPrintString("Next detection time: %fs" % GLOBALS.detection_time)

    # This is needed to address VMS texts
    GLOBALS.vms_message_att = ANGConnGetAttribute(AKIConvertFromAsciiString("GKVMS::currentMessageAtt"))
    logger.debug("AAPIInit() end")
    return 0


def AAPIManage(timeSim, timeSta, timTrans, acicle):
    # Return immediately in case of warm-up phase
    if timeSim < timTrans:
        return 0
    # Acquire global lock so that the receiving thread may process the data batch at once
    # TODO: Does not work
    # GLOBALS.lock.acquire()
    # Check if there is a command from the control system pending
    got_data = False
    #logging.debug("AAPIManage at %f" % time)
    try:
        # This loop will exit on Exception in the moment that the data queue is empty
        while True:
            id_gantry_server, command = INTERFACE.get_command()
            GLOBALS.gantry_servers[id_gantry_server].process_command(command)
            got_data = True
    except gi.NoData:
        if got_data:
            AKIPrintString("[%f,%f,%f,%f] no further data available" % (timeSim, timeSta, timTrans, acicle))
        pass
    #GLOBALS.lock.release()
    #logger.debug("AAPIManage returning")
    return 0


def AAPIPostManage(timeSim, timeSta, timTrans, acicle):
    # Return immediately in case of warm-up phase
    if timeSim < timTrans:
        return 0
    # Check if we shall provide the detector readings
    if timeSim >= GLOBALS.detection_time:
        # Read all detectors for all vehicles
        dets = []
        for (id_detector,name) in GLOBALS.detectors:
            count = {0:0}
            speed = {0:0}
            occup = {0:0}
            for id_vehicletype in xrange(GLOBALS.num_vehicle_types + 1):
                count[id_vehicletype+1] = AKIDetGetCounterAggregatedbyId(id_detector, id_vehicletype)
                speed[id_vehicletype+1] = AKIDetGetSpeedAggregatedbyId(id_detector, id_vehicletype)
                occup[id_vehicletype+1] = AKIDetGetTimeOccupedAggregatedbyId(id_detector, id_vehicletype)
            # Vehicle type 0 which goes to index 1 is treated as "other" in SIRID, but the original zero
            # index means all vehicle in Aimsun. SIRID indexes this information as vehicle class 9.
            # TODO: Check the names of vehicle classes so that te classes may be mapped correctly
            count[9] = count[1]
            speed[9] = speed[1]
            occup[9] = speed[1]
            # Index 1 in SIRID denotes motorcycles and we do not simulate motorcycles.
            count[1] = 0
            speed[1] = 0
            occup[1] = 0
            dets.append((name, GLOBALS.gantry_ld_map[name], (count, speed, occup)))
        time_tuple = time.localtime(GLOBALS.time_offset+timeSim-timTrans)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)
        measurements = (time_str, dets)
        AKIPrintString("Data at %.1fs: %s" % (timeSim, repr(dets)))
        INTERFACE.put_measurements(measurements)
        # Move last detection time
        GLOBALS.detection_time += GLOBALS.detection_interval
        AKIPrintString("Next detection time: %fs" % GLOBALS.detection_time)
    return 0


def AAPIFinish():
    #global fout
    #fout.close()
    AKIPrintString("AAPIFinish()")
    return 0


def AAPIUnLoad():
    AKIPrintString("AAPIUnLoad()")
    return 0


def AAPIEnterVehicle(idveh, idsection):
    return 0


def AAPIExitVehicle(idveh, idsection):
    return 0


def AAPIPreRouteChoiceCalculation(time, timeSta):
    # AKIPrintString("AAPIPreRouteChoiceCalculation() pass")
    return 0


def AAPIEnterVehicleSection(idveh, idsection, atime):
    # AKIPrintString("AAPIEnterVehicleSection() pass")
    return 0


def AAPIExitVehicleSection(idveh, idsection, atime):
    # AKIPrintString("AAPIExitVehicleSection() pass")
    return 0

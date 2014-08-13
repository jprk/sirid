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
fh = logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aapi_gantry.log'), mode='w')
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
    actions = defaultdict(dict)
    vms_message_att = None
    gantry_ld_map = dict()
    gantry_obj_id = dict()
    time_offset = 0
    lane_map = defaultdict(dict)

SYMBOLS = dict(
    A=['Zhasnuto', 'A8 -Nebezpečí smyku', 'A15 -Práce na silnici', 'A22 -Jiné nebezpečí', 'A23 - Tvorba kolon',
       'A24 - Náledí', 'A26 – Mlha', 'A27 – Nehoda'],
    B=['Zhasnuto', '120', '100', '80', '60'],
    F=['Zhasnuto', 'Zákaz vjezdu NV', 'Šipka vlevo', 'Šipka vpravo', 'Konec omezení'],
    EA=['Zhasnuto', '500m', '1000m', '1500m', '2000m', '2500m', '3000m', '3500m', '4000m', '4500m', '5000m', '5500m',
        '6000m', '6500m', '7000m', '7500m', '8000m', '8500m', '9000m', '9500m', '10000m'],
    EF=['Zhasnuto', '3,5t', '6t', '7,5t', '9t', '12t'])

# Line map for right-hand direction and two-lane road. All traffic signs located on the right shoulder are supposed to
# be related to the right lane, all traffic signs located on the left shoulder are related to the left lane.
LANE_MAP_R2 = {9:2, 3:1, 1:1}

# Line map for left-hand direction and two-lane road. All traffic signs located on the shoulder are supposed to
# be related to the right lane.
LANE_MAP_L2 = {0:2, 4:1, 2:1}

# Line map for right-hand direction and three-lane road. All traffic signs located on the shoulder are supposed to
# be related to the right lane.
LANE_MAP_R3 = {9:3, 5:2, 3:1, 1:1}

# Line map for left-hand direction and two-lane road. All traffic signs located on the shoulder are supposed to
# be related to the right lane.
LANE_MAP_L3 = {0:3, 6:2, 4:1, 2:1}

# These constants are used for change speed action
ALL_SEGMENTS = -1
COMPLIANCE_LEVEL = 1.0 # 0.85

# This is the global interface module that facilitates IPC between Gantry
# server module and Aimsun
INTERFACE = gi.GantryInterface()

# Global variables are ugly, evil, but in AAPI we have no mechanism to avoid
# global storage. Pity.
GLOBALS = Globals()


# class GantryRequest(SocketServer.StreamRequestHandler):
#     """
#     The RequestHandler class for the server.
#
#     It is instantiated once per connection to the server, and must override the
#     handle() method to implement communication to the client. We make use of an
#     alternative handler class that makes use of streams, which are file-like
#     objects that simplify communication by providing the standard file interface.
#     The server is single threaded, which means that only one client is allowed
#     to connect at a time.
#     """
#
#     def handle(self):
#         print "-- handler started for connection from %s" % str(self.client_address)
#         # Infinite loop serving the requests from the SIRID hub.
#         print "   reading a command"
#         data = self.rfile.read()
#         print "   putting the command into a queue"
#         print data
#
# def gantry_socket_server():
#     t = threading.current_thread()
#     AKIPrintString("%s: gantry_socket_server thread started" % t.name)
#     # Send response to the sirid server process that we are up and running
#     sirid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sirid_socket.connect(('localhost', 1251))
#     sirid_socket.sendall('AIMSUN_UP_AND_RUNNING')
#     AKIPrintString("%s: sent message to sirid server" % t.name)
#
#     # Now enter the loop processing commands
#     while True:
#         data = sirid_socket.recv(1024)
#         if data == '@LOCK':
#             AKIPrintString("%s: locking other threads" % t.name)
#             #GLOBALS.lock.acquire()
#             AKIPrintString("%s: locked other threads" % t.name)
#         elif data == '@UNLOCK':
#             AKIPrintString("%s: unlocking other threads" % t.name)
#             #GLOBALS.lock.release()
#             AKIPrintString("%s: unlocked other threads" % t.name)
#         elif data == '@EXIT':
#             AKIPrintString("%s: exit requested" % t.name)
#         else:
#             AKIPrintString("%s: Received data `%s`" % (t.name, repr(data)))
#             id_gantry_server, command = pickle.loads(data)
#             GLOBALS.gantry_servers[id_gantry_server].process_command(command)
#             AKIPrintString("%s: Received command `%s`" % (t.name, repr(command)))
#
#         AKIPrintString("%s: looping back to next recv()" % t.name)
#
#     AKIPrintString("%s: closing socket" % t.name)
#     sirid_socket.close()
#     # Create the server, binding to localhost on port 9999
#     #server = SocketServer.TCPServer((HOST, PORT), GantryRequest)
#     #server.timeout = 30
#     #AKIPrintString("%s: handle_request()" % t.name)
#     #server.handle_request()
#     AKIPrintString("%s: exitting" % t.name)


def change_vms_text(gantry_server_id_set):
    """Change the text message shown at VMS identified by `params`."""
    logger.debug("change_vms_text(): updating gantry servers %s" % repr(gantry_server_id_set))
    # To set something the be displayed on a VMS is quite obscure. See
    # https://groups.yahoo.com/neo/groups/Aimsun/conversations/topics/4123
    for gantry_server_id in gantry_server_id_set:
        # A single VMS in Aimsun represents a gantry holding several variable message signs in reality.
        message_dict = GLOBALS.gantry_servers[gantry_server_id].get_gantry_messages()
        for gantry_id in message_dict:
            AKIPrintString("cmd :: changing vms text on %s/%s" % (gantry_server_id, gantry_id))
            logger.debug("change_vms_text(): changing text on %s/%s" % (gantry_server_id, gantry_id))
            # Convert the gantry object name to the numerical object id
            id_gantry_obj = GLOBALS.gantry_obj_id[gantry_id]
            # Display the messages
            ANGConnSetAttributeValueStringA(
                GLOBALS.vms_message_att, id_gantry_obj, message_dict[gantry_id])


def apply_speed_limit(gantry_server_id_set):
    """Apply the speed limit for lanes following the gantry"""
    logger.debug("apply_speed_limit(): updating gantry servers %s" % repr(gantry_server_id_set))
    for gantry_server_id in gantry_server_id_set:
        # A single VMS in Aimsun represents a gantry holding several variable message signs in reality.
        speed_dict = GLOBALS.gantry_servers[gantry_server_id].get_speed_limits()
        for gantry_id in speed_dict:
            # Get a list of change speed action entries
            logger.debug('apply_speed_limit(): processing gantry %s/%s' % (gantry_server_id, gantry_id))
            for sign_id, lane_id, new_speed, vehicle_type in speed_dict[gantry_id]:
                # Value of lane_id label follows the EDS convention of marking the lanes 9,3,1 or 9,5,3,1
                # and 0,4,2 or 0,6,4,2 respectively. Aimsun counts lanes starting at the outside towards
                # the left lane, hence in both left and right directions the appropriate Aimsun lane ids
                # would be 2,1,- or
                id_aimsun_lane = GLOBALS.lane_map[gantry_id][lane_id]
                # Get the change speed action data
                AKIPrintString("cmd :: changing speed limit on gantry %s sign %s" % (gantry_id, sign_id))
                logger.debug("apply_speed_limit(): testing speed change on %s/%s lane %d (Aimsun: lane %d) vehicle type %d" %
                             (gantry_id, sign_id, lane_id, id_aimsun_lane, vehicle_type))
                # Loop over all sections that follow this gantry until the next gantry and set the limit
                # for the given lane
                for id_section in GLOBALS.sections[gantry_id]:
                    # If there was an previous change speed action, disable it
                    action_handle = GLOBALS.actions[id_section][id_aimsun_lane]
                    if action_handle:
                        logger.debug("actions[%d][%d] - removing previous speed action %s" %
                                     (id_section, id_aimsun_lane, repr(action_handle)))
                        AKIActionRemoveAction(action_handle)
                        GLOBALS.actions[id_section][id_aimsun_lane] = None
                    # Set the speed limit in case that the command is not zero
                    if new_speed:
                        action_handle = AKIActionAddDetailedSpeedAction(
                            id_section, id_aimsun_lane, ALL_SEGMENTS, new_speed, vehicle_type, COMPLIANCE_LEVEL)
                        if not action_handle:
                            logger.error("cannot add change speed action [%d][%d]" % (id_section, id_aimsun_lane))
                            raise ValueError("cannot add change speed action [%d][%d]" % (id_section, id_aimsun_lane))
                        GLOBALS.actions[id_section][id_aimsun_lane] = action_handle
                        logger.debug("actions[%d][%d] - added speed action %s (sign %s, speed %f km/h)" %
                                     (id_section, id_aimsun_lane, repr(action_handle), sign_id, new_speed))


def AAPILoad():
    """


    :return:
    """
    try:
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
        #tree = Et.parse(os.path.join(mod_dir, '../sokp/sokp_v7.xml'))
        tree = Et.parse(os.path.join(mod_dir, 'sokp.xml'))
        root = tree.getroot()
        AKIPrintString("sirid.xml root element: &gt;" + repr(root)[1:-1] + "&lt;")

        GLOBALS.gantry_servers = {}
        GLOBALS.gantry_ld_map = {}
        for gantry_node in root:
            #print gantry_node.tag, gantry_node.attrib
            id_gantry = gantry_node.attrib['id']
            gantry_server = GantryServer(id_gantry)
            for device in gantry_node:
                #print ' ', device.tag, device.attrib
                id_device = int(device.attrib['id'])
                try:
                    device_type = device.attrib['type']
                except KeyError:
                    device_type = ''
                ppk = device.attrib['ppk']
                for sub_device in device:
                    #print '   ', sub_device.tag, sub_device.attrib
                    id_sub_device = int(sub_device.attrib['id'])
                    sub_device_type = sub_device.attrib['type']
                    try:
                        sub_device_description = sub_device.attrib['description']
                    except KeyError:
                        sub_device_description = ''
                    prefix = sub_device.attrib['prefix']
                    sub_instance = gantry_server.add_sub_device(id_device, ppk, id_sub_device, sub_device_type, prefix)
                    # We need a mapping from detector id to gantry, device, subdevice
                    if isinstance(sub_instance, GantryLoopDetector):
                        for loop_detector in sub_device:
                            # print '       ', loop_detector.tag, loop_detector.attrib
                            id_lane = int(loop_detector.attrib['id'])
                            det_type = loop_detector.attrib['type']
                            position = loop_detector.attrib['position']
                            prefix = loop_detector.attrib['prefix']
                            logger.debug("  added gantry_ld_map['%s']" % prefix)
                            GLOBALS.gantry_ld_map[prefix] = \
                                (id_gantry, id_device, device_type, id_sub_device,
                                 sub_device_type, sub_device_description, id_lane, det_type, position, prefix)
            GLOBALS.gantry_servers[id_gantry] = gantry_server
            # A gantry server may service more than a single gantry. Physical gantries are labeled 'P0000' and
            # their names are constructed during the process of adding devices and sub-devices to the GantryServer
            # node.
            for gantry_label in gantry_server.get_gantry_labels():
                ushort_label = AKIConvertFromAsciiString(gantry_label)
                object_id = ANGConnGetObjectId(ushort_label, True)
                if object_id < 0:
                    raise KeyError("Gantry label '%s' not found, error code %d" % (gantry_label,object_id))
                GLOBALS.gantry_obj_id[gantry_label] = object_id
                logger.debug('gantry label %s is Aimsun object %d' % (gantry_label, object_id))
            # Initial setup of VMS messages to their default values will be done in AAPIInit().
            # #print gantry_server.get_gantry_messages()

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
    except:
        e_type, e_val, e_trace = sys.exc_info()
        AKIPrintString('Exception occured: %s (%s)' % (repr(e_type), repr(e_val)))
        logger.exception('exception in AAPILoad')
    return 0


def AAPIInit():
    """


    :return:
    """
    try:
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
            # The name of the object can contain extended information after the section id,
            # the information has to be separated by space.
            if name:
                name = name.split()[0]
            # Every section behind a gantry has a name that follows the `Sdyyyy.n` format,
            # where the numeric `dyyyy` part corresponds to the numeric part of the gantry
            # name
            m = section_re.match(name)
            if m:
                # There has been a match
                gantry_id = 'P'+m.group(1)
                # Get section informaton, we need the number of lanes
                section_info = AKIInfNetGetSectionANGInf(id_object)
                if section_info.report:
                    raise IndexError('AKIInfNetGetSectionANGInf(%d) returns status %d' %
                                     (id_object, section_info.report))
                logger.debug("section %s (%d) - %d central lanes, %d side lanes" %
                             (name, id_object, section_info.nbCentralLanes, section_info.nbSideLanes))
                # Append the internal numeric ID to a list of sections governed by that gantry
                GLOBALS.sections[gantry_id].append(id_object)
                # Do this only for sections ending with .1 - these are sections immediately following the
                # gantry and therefore their configuration corresponds to the configuration of VMS on the
                # gantry itself
                if name[-1] == '1':
                    # Remember the number of lanes
                    num_lanes = section_info.nbCentralLanes
                    # Determine the direction of this section
                    is_direction_right = int(name[1])
                    # Update the lane id map that converts EDS lane id to Aimsun lane id, taking into account
                    # different lane counts
                    if num_lanes == 2:
                        if is_direction_right:
                            # The right-hand part
                            GLOBALS.lane_map[gantry_id] = LANE_MAP_R2
                            logger.debug("section %s (%d) - using LANE_MAP_R2" % (name, id_object))
                        else:
                            # The left-hand part
                            GLOBALS.lane_map[gantry_id] = LANE_MAP_L2
                            logger.debug("section %s (%d) - using LANE_MAP_L2" % (name, id_object))
                    elif num_lanes == 3:
                        if is_direction_right:
                            # The right-hand part
                            GLOBALS.lane_map[gantry_id] = LANE_MAP_R3
                            logger.debug("section %s (%d) - using LANE_MAP_R3" % (name, id_object))
                        else:
                            # The left-hand part
                            GLOBALS.lane_map[gantry_id] = LANE_MAP_L3
                            logger.debug("section %s (%d) - using LANE_MAP_L3" % (name, id_object))
                    else:
                        raise ValueError('allowed number of central lanes for section %s is 2 or 3')
                # Remember that this section follows a gantry. The list that we careate here will be
                # populated by lane information after all "interesting" sections have been processed
                GLOBALS.actions[id_object] = None
                logger.debug("section %s (%d) - creating empty actions[%s][%d]" %
                             (name, id_object, gantry_id, id_object))
            #
            AKIPrintString("  [%d] %d / `%s`" % (pos, id_object, name))

        # Populate GLOBALS.actions with lane count corresponding to the first section after the gantry.
        # This way we will ignore the "extra" side lanes added before intersections, for example.
        for gantry_id in GLOBALS.lane_map:
            # Get the number of lanes
            num_lanes = len(GLOBALS.lane_map[gantry_id])-1
            for id_section in GLOBALS.sections[gantry_id]:
                if num_lanes == 2:
                    GLOBALS.actions[id_section] = {1:None, 2:None}
                    logger.debug("gantry[%s][%d] has two lanes" % (gantry_id, id_section))
                elif num_lanes == 3:
                    GLOBALS.actions[id_section] = {1:None, 2:None, 3:None}
                    logger.debug("gantry[%s][%d] has three lanes" % (gantry_id, id_section))
                else:
                    raise ValueError('allowed number of lanes for section %d is 2 or 3')

        #
        #  List all detectors.
        #
        # Construct a regular expressions for matching the "interesting" detector names
        detector_re = re.compile(r"LD(\d\d\d\d\d)")
        # It could happen that not all detectors with name that matches the above regular
        # expression shall be reported back to the control system. The list of "active"
        # detectors is given by the keys of `gantry_ld_map`
        reported_detector_names = GLOBALS.gantry_ld_map.keys()
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
                # There has been a match, get the detector name
                detector_name = m.group()
                # Check that the detector name is listed in the list of detectors that shall be
                # reported back
                if detector_name in reported_detector_names:
                    # Append the internal numeric ID and detector name to a list of detectors that
                    # will be reported back to the upper control level
                    GLOBALS.detectors.append((id_object, detector_name))
                    logger.debug("GLOBALS.detectors.append(%d,%s)" % (id_object, detector_name))
                else:
                    logger.debug("detector (%d,%s) ignored" % (id_object, detector_name))
            #
            AKIPrintString("  [%d] %d / `%s`" % (pos, id_object, name))

        #
        #  List all gantries.
        #
        # Construct a regular expressions for matching the "interesting" detector names
        gantry_re = re.compile(r"P(\d\d\d\d\d)")

        # List all vehicle types.
        # Sadly the names of vehicle types cannot be obtained in Python
        GLOBALS.num_vehicle_types = AKIVehGetNbVehTypes()
        AKIPrintString("Got %d vehicle types:" % GLOBALS.num_vehicle_types)
        logger.debug("Got %d vehicle types:" % GLOBALS.num_vehicle_types)

        # Remember the detection interval of detectors
        GLOBALS.detection_interval = AKIDetGetIntervalDetection()
        AKIPrintString("Detection interval: %fs" % GLOBALS.detection_interval)
        logger.debug("Detection interval: %fs" % GLOBALS.detection_interval)

        # Compute the first timestamp of valid detector measurement
        GLOBALS.detection_time = GLOBALS.detection_interval + AKIGetDurationTransTime()
        AKIPrintString("Next detection time: %fs" % GLOBALS.detection_time)
        logger.debug("Next detection time: %fs" % GLOBALS.detection_time)

        # This is needed to address VMS texts
        GLOBALS.vms_message_att = ANGConnGetAttribute(AKIConvertFromAsciiString("GKVMS::currentMessageAtt"))

        # And now we can display default texts on all VMS signs.
        change_vms_text(GLOBALS.gantry_servers.keys())

        logger.debug("AAPIInit() end")
    except:
        e_type, e_val, e_trace = sys.exc_info()
        AKIPrintString('Exception occured: %s (%s)' % (repr(e_type), repr(e_val)))
        logger.exception('exception in AAPILoad')
    return 0


def AAPIManage(timeSim, timeSta, timTrans, acicle):
    # Return immediately in case of warm-up phase
    if timeSim < timTrans:
        return 0
    # Acquire global lock so that the receiving thread may process the data batch at once
    # TODO: Does not work
    # GLOBALS.lock.acquire()
    logger.debug("AAPIManage() at %.1f" % timeSim)
    # Check if there is a command from the control system pending
    got_data = False
    gantry_update_set = set()
    try:
        # This loop will exit on Exception in the moment that the data queue is empty
        while True:
            id_gantry_server, command = INTERFACE.get_command()
            logger.debug("gantry %s command %s" % (id_gantry_server, repr(command)))
            GLOBALS.gantry_servers[id_gantry_server].process_command(command)
            gantry_update_set.add(id_gantry_server)
            got_data = True
    except gi.NoData:
        if got_data:
            AKIPrintString("[%f,%f,%f,%f] no further data available" % (timeSim, timeSta, timTrans, acicle))
            apply_speed_limit(gantry_update_set)
            change_vms_text(gantry_update_set)
        pass
    except:
        e_type, e_val, e_trace = sys.exc_info()
        AKIPrintString('Exception occurred: %s (%s)' % (repr(e_type), repr(e_val)))
        logger.exception('exception in AAPIManage')
    #GLOBALS.lock.release()
    logger.debug("AAPIManage() returning")
    return 0


def AAPIPostManage(timeSim, timeSta, timTrans, acicle):
    try:
        # Return immediately in case of warm-up phase
        if timeSim < timTrans:
            return 0
        # Check if we shall provide the detector readings
        logger.debug("AAPIPostManage() at %.1f" % timeSim)
        if timeSim >= GLOBALS.detection_time:
            logger.debug("AAPIPostManage reading out detectors")
            # Read all detectors for all vehicles
            dets = []
            for (id_detector,name) in GLOBALS.detectors:
                logger.debug("  %d,%s" % (id_detector,name))
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
                try:
                    dets.append((name, GLOBALS.gantry_ld_map[name], (count, speed, occup)))
                except KeyError as e:
                    logger.exception("Cannot append detector info")

            time_tuple = time.localtime(GLOBALS.time_offset + timeSim - timTrans)
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)
            measurements = (time_str, dets)
            AKIPrintString("Data at %.1fs: %s" % (timeSim, repr(dets)))
            logger.debug("dispatching data at %.1f seconds" % timeSim)
            INTERFACE.put_measurements(measurements)
            # Move last detection time
            GLOBALS.detection_time += GLOBALS.detection_interval
            AKIPrintString("Next detection time: %fs" % GLOBALS.detection_time)
            logger.debug("next detection time at %.1f seconds" % GLOBALS.detection_time)
            # If the simulation is running in a synchronous mode, the simulator now has to wait until a new command
            # from the controller arrives. This may be tricky as the controller may find everything okay and no
            # control action to be necessary, but it has to be done anyway
            if INTERFACE.is_synchronous():
                INTERFACE.wait_on_control_action()
    except:
        AKIPrintString("Unexpected error, see log file for more information:")
        logger.exception("Unexpected error")
        raise
    logger.debug("AAPIPostManage() returning")
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

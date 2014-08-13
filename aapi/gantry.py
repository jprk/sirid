#!/usr/bin/python
# -*- coding: windows-1250 -*-

import re
import xml.etree.ElementTree as Et
from collections import defaultdict

SYMBOLS = {
    'A': ['Zhasnuto', 'A8 -Nebezpečí smyku', 'A15 -Práce na silnici', 'A22 -Jiné nebezpečí', 'A23 - Tvorba kolon',
          'A24 - Náledí', 'A26 – Mlha', 'A27 – Nehoda'],
    'B': ['Zhasnuto', '120', '100', '80', '60'],
    'F': ['Zhasnuto', 'Zákaz vjezdu NV', 'Šipka vlevo', 'Šipka vpravo', 'Konec omezení'],
    'EA': ['Zhasnuto', '500m', '1000m', '1500m', '2000m', '2500m', '3000m', '3500m', '4000m', '4500m', '5000m', '5500m',
           '6000m', '6500m', '7000m', '7500m', '8000m', '8500m', '9000m', '9500m', '10000m'],
    'EF': ['Zhasnuto', '3,5t', '6t', '7,5t', '9t', '12t']}

LANE_ID_TO_STR = {
    0: 'left',
    2: 'shoulder',
    4: 'right',
    6: 'middle',
    1: 'shoulder',
    3: 'right',
    5: 'middle',
    9: 'left'}

CATEGORY = [
    {'id': '0', 'type': '-?-', 'description': 'others'},
    {'id': '1', 'type': 'mot', 'description': 'motorcycle'},
    {'id': '2', 'type': 'car', 'description': 'car'},
    {'id': '3', 'type': 'c+t', 'description': 'car_with_trailer'},
    {'id': '4', 'type': 'van', 'description': 'delivery_van'},
    {'id': '5', 'type': 'lor', 'description': 'truck'},
    {'id': '6', 'type': 'h+t', 'description': 'truck_with_trailer'},
    {'id': '7', 'type': 'trc', 'description': 'semitrailer_truck'},
    {'id': '8', 'type': 'bus', 'description': 'bus'},
    {'id': '9', 'type': 'all', 'description': 'all'}]


class GantrySubDevice:
    """Represents a single gantry sub-device, that is, a signalling element.

    The signalling element may be of different type - variable message sign (VMS) represented
    as a text field, pre-defined road sign (speed limit, lane closure etc)."""
    MESSAGES = []
    PREFIX = ''
    TYPE = ''

    # This is a kind of abstract class which wraps functionality of child classes. In order to
    # conveniently create them, a factory method is used
    @staticmethod
    def factory(prefix, id_sub_device, id_type):
        """

        :param prefix:
        :param id_type:
        :param id_sub_device:
        :return: :raise ValueError:
        """
        if GantryWarningSign.is_acceptable(prefix, id_type):
            return GantryWarningSign(prefix, id_sub_device, id_type)
        elif GantrySpeedLimit.is_acceptable(prefix, id_type):
            return GantrySpeedLimit(prefix, id_sub_device, id_type)
        elif GantryRegulatorySign.is_acceptable(prefix, id_type):
            return GantryRegulatorySign(prefix, id_sub_device, id_type)
        elif GantryWarningInfo.is_acceptable(prefix, id_type):
            return GantryWarningInfo(prefix, id_sub_device, id_type)
        elif GantryRegulatoryInfo.is_acceptable(prefix, id_type):
            return GantryRegulatoryInfo(prefix, id_sub_device, id_type)
        elif GantryLoopDetector.is_acceptable(prefix, id_type):
            return GantryLoopDetector(prefix, id_sub_device, id_type)
        else:
            raise ValueError('incompatible prefix and type of gantry sub-device')

    # This is used to find whether the combination of id_type and prefix can be used to create
    # the class in concern
    @classmethod
    def is_acceptable(cls, prefix, id_type):
        """

        :param prefix:
        :param id_type:
        :return:
        """
        return (prefix[0] == cls.PREFIX) and (id_type in cls.TYPE)

    # Initialise a gantry sub-device object
    def __init__(self, prefix, id_sub_device, id_type):
        # Make sure that variable types fit
        assert isinstance(prefix, str)
        assert isinstance(id_sub_device, int)
        assert isinstance(id_type, str)
        # Initialise object
        self.prefix = prefix
        self.id = id_sub_device
        self.id_type = id_type
        self.num_messages = len(self.MESSAGES)
        # Initial state corresponds to message id 0
        self.message_id = 0
        # By default the device displays message text
        self.has_message_text = True
        # Nothing has been measured
        self.measurements = None

    # Get command
    def set_message_id(self, id_message):
        """


        :rtype : str
        :param id_message:
        :return: :raise ValueError:
        """
        if self.has_message_text:
            if id_message < 0 or id_message >= self.num_messages:
                raise ValueError('unsuported command %d on sub-device %d' % (id_message, self.id))
            self.message_id = id_message
        else:
            raise TypeError('cannot set message text on devices that do not support it')

    # Get message text
    def get_message_text(self):
        return self.MESSAGES[self.message_id]

    # Get sub-device prefix:
    def get_prefix(self):
        """Get prefix of the sub-device.

        :rtype : str
        :return:
        """
        return self.prefix

    def set_measurements(self, measurements):
        self.measurements = measurements


class GantryWarningSign(GantrySubDevice):
    """Warning sign at some position on the gantry display."""
    # Messages (traffic signs) displayed
    MESSAGES = ['Zhasnuto', 'A8 -Nebezpečí smyku', 'A15 -Práce na silnici', 'A22 -Jiné nebezpečí',
                'A23 - Tvorba kolon', 'A24 - Náledí', 'A26 – Mlha', 'A27 – Nehoda']
    # Gantry sub-device type
    TYPE = ['LED', 'LED+DT']
    PREFIX = 'A'


class GantryWarningInfo(GantrySubDevice):
    """Additional information to a warning sign at some position on the gantry display."""
    # Messages (traffic signs) displayed
    MESSAGES = ['Zhasnuto', '500m', '1000m', '1500m', '2000m', '2500m', '3000m', '3500m', '4000m',
                '4500m', '5000m', '5500m', '6000m', '6500m', '7000m', '7500m', '8000m', '8500m',
                '9000m', '9500m', '10000m']
    # Gantry sub-device type
    TYPE = ['DT']
    # In fact the prefix should be 'EA' but it seems that gantries at SOKP use 'A'
    PREFIX = 'A'


class GantrySpeedLimit(GantrySubDevice):
    """Speed limit regulatory sign at some position on the gantry display."""
    # Messages (traffic signs) displayed
    MESSAGES = ['Zhasnuto', '120', '100', '80', '60']
    # Speed limits corresponding to messages
    SPEED_LIMITS = [None, 120, 100, 80, 60]
    # Gantry sub-device type
    TYPE = ['LED']
    PREFIX = 'B'

    def __init__(self, prefix, id_sub_device, id_type):
        """

        :type self: GantryLoopDetector
        """
        GantrySubDevice.__init__(self, prefix, id_sub_device, id_type)
        self.id_lane = int(prefix[1])

    def get_speed_limit(self):
        """Return a tuple containing speed limit information"""
        # TODO Figure out how to check which class of vehicles this limit applies to.
        # For the time being we expect all vehicles to be forced to keep the speed limit.
        return self.prefix, self.id_lane, self.SPEED_LIMITS[self.message_id], 0


class GantryRegulatorySign(GantrySubDevice):
    """Regulatory sign other than a speed limit at some position on the gantry display."""
    # Messages (traffic signs) displayed
    MESSAGES = ['Zhasnuto', 'Zákaz vjezdu NV', 'Šipka vlevo', 'Šipka vpravo', 'Konec omezení']
    # Gantry sub-device type
    TYPE = ['LED', 'LED+DT']
    # Gantry sub-device type
    PREFIX = 'F'


class GantryRegulatoryInfo(GantrySubDevice):
    """Additional info for a regulatory sign at some position on the gantry display."""
    # Messages (traffic signs) displayed
    MESSAGES = ['Zhasnuto', '3,5t', '6t', '7,5t', '9t', '12t']
    # Gantry sub-device type
    TYPE = ['DT']
    # In fact the prefix should be 'EF' but it seems that gantries at SOKP use 'F'
    PREFIX = 'F'


class GantryLoopDetector(GantrySubDevice):
    """Loop detector subdevice that does not display anything on the VMS display."""

    TYPE = ['LD4']
    # In fact the prefix should be 'LD4' but we compare only the first character
    PREFIX = 'L'

    def __init__(self, prefix, id_sub_device, id_type):
        """

        :type self: GantryLoopDetector
        """
        GantrySubDevice.__init__(self, prefix, id_sub_device, id_type)
        self.id_lane = int(prefix[3])
        self.str_lane = LANE_ID_TO_STR[self.id_lane]
        self.has_message_text = False


class GantryDevice:
    """A single gantry device: a sign, a sign with an info table, text display, ..."""

    def __init__(self, id_device, ppk):
        self.id = id_device
        self.ppk = ppk
        self.sub_devices = dict()

    def add_sub_device(self, id_sub_device, id_type, prefix):
        """


        :rtype : GantrySubDevice
        :param id_sub_device:
        :param id_type:
        :param prefix:
        :return: :raise TypeError:
        """
        # As the GantrySubDevice object needs id, type, and prefix to initialise, we cannot use a dict
        # sub-class or defaultdict().
        if id_sub_device in self.sub_devices:
            raise TypeError(
                "Gantry device %s (id:%d) already has a sub-device with id %d" % (self.ppk, self.id, id_sub_device))
        else:
            # Create a new device
            sub_device = self.sub_devices[id_sub_device] = GantrySubDevice.factory(prefix, id_sub_device, id_type)
        return sub_device

    def get_sub_device_id_list(self):
        """


        :return:
        """
        return sorted(self.sub_devices)

    def has_sub_device(self, id_sub_device):
        """

        :param id_sub_device:
        :rtype : bool
        :return:
        """
        return id_sub_device in self.sub_devices

    def get_sub_device(self, id_sub_device):
        """


        :rtype : GantrySubDevice
        :param id_sub_device:
        :return:
        """
        return self.sub_devices[id_sub_device]


class Gantry:
    "Object representation of a single highway gantry holding several signalling elements."

    def __init__(self, id_gantry):
        self.id = id_gantry
        self.devices = dict()

    def add_device(self, id_device, ppk):
        """


        :rtype : GantryDevice
        :param id_device: 
        :param ppk: 
        :return: :raise TypeError: 
        """
        # As the GantryDevice object needs id and ppk to initialise, we cannot use a dict
        # sub-class or defaultdict().
        if id_device in self.devices:
            raise TypeError("Gantry %s already has a device %d with ppk %s" % (self.id, id_device, ppk))
        else:
            # Create a new device
            device = self.devices[id_device] = GantryDevice(id_device, ppk)
        return device

    def has_device(self, id_device):
        return id_device in self.devices

    def get_device_id_list(self):
        """


        :return:
        """
        return sorted(self.devices)

    def get_device(self, id_device):
        """


        :rtype : GantryDevice
        :param id_device:
        :return:
        """
        return self.devices[id_device]


class gantrydict(dict):
    """An extension to dict() that creates a gantry object in case it does not exist.
    In this case we need to pass the key of the missing entry to the constructor of
    Gantry object, hence we cannot use defaultdict().

    See http://stackoverflow.com/questions/7963755/using-the-key-in-collections-defaultdict
    """

    def __missing__(self, key):
        value = self[key] = Gantry(key)
        return value


class GantryServer:
    """Object representation of a single highway gantry that holds a set of variable message
    signs.

    Device is local to a gantry server.
    Sub-devices are local to gantries.

    The gantry object maintains a state of all its subordinate VMSs and allows for modification
    of the state and its conversion to a meaningful text representation."""

    def __init__(self, id_gantry_server):
        self.id = id_gantry_server
        # self.state = defaultdict(dict)
        #self.prefixes = dict()
        #self.ppks = defaultdict(dict)
        self.gantry_devices = defaultdict(list)
        self.gantries = gantrydict()
        #self.gantry_names = list()
        #self.gantry_devices = dict()
        self.gantry_pos_re = re.compile(r"[A-Z]+(\d)(\d\d\d\d)")
        self.gantry_neg_re = re.compile(r"[A-Z]+(\d)(\dM\d\d)")

    def locate_sub_device(self, id_device, id_sub_device):
        """Return an instance of GantrySubDevice for the given (device, sub-device) pair.

        As the GantryServer instance may be responsible for several physical gantries, represented
        by Gantry instances, and as a GantryDevice, although unique for a gantry server, may span
        over several physical gantries (LD4 devices, for example, have a global device id 20 and
        a sub-device 0 on one physical gantry, while sub-device 1 resides on a gantry located in
        the opposite direction), several partial instances of the same GantryDevice may exist,
        each of them holding a sub-set of the sub-devices specified for the given device. The
        purpose of this method is to go through all Gantry instances, locate the instance where
        the (device, sub-device) pair exists and return the GantrySubDevice instance corresponding
        to the pair.

        :rtype : GantrySubDevice
        :param id_device: int
        :param id_sub_device: int
        """
        sub_device = None
        for gantry in self.gantry_devices[id_device]:
            device = gantry.get_device(id_device)
            if device.has_sub_device(id_sub_device):
                sub_device = device.get_sub_device(id_sub_device)
                break
        if not sub_device:
            raise KeyError("Unknown (device, sub-device) pair ({:d},{:d}) on gantry server {:s}".format(
                id_device, id_sub_device, self.id))
        return sub_device


    def add_sub_device(self, id_device, ppk, id_sub_device, id_type, prefix):
        # Match the regular expression describing the device prefix which corresponds to gantry id
        m = self.gantry_pos_re.match(prefix)
        # In case of no match in the "positive" prefix try also the variant with negative stationing
        if not m:
            # Match the regular expression describing the device prefix which corresponds to gantry id
            # with negative stationing
            m = self.gantry_neg_re.match(prefix)
            # In case of no match raise an error
            if not m:
                raise ValueError("device prefix does not match template")
        # The first digit matched is the lane number. Odd lane numbers correspond to left-hand
        # lanes in the direction of infrastructure stationing, even lane numbers are used for
        # devices installed in right-hand lanes. Together with the next four stationing digits
        # the device prefix forms the numeric part of gantry name
        id_gantry = 'P' + str(int(m.group(1)) % 2) + m.group(2)
        # Get the gantry object corresponding to `id_gantry`. This will create an empty Gantry
        # object in case that self.gantries does not hold the given id.
        gantry = self.gantries[id_gantry]
        # Get the gantry device object
        # TODO: A single device on a gantry server is now supposed to exist only on a singe gantry. However, this
        # is not true in reality, at least LD4 boards occupy a single device 20 that exists across all gantries
        if gantry.has_device(id_device):
            device = gantry.get_device(id_device)
        else:
            device = gantry.add_device(id_device, ppk)
            # We need a direct link from gantry server to a device
            # TODO: original: if id_device in self.devices: because we thought that a device may exist only on
            # single gantry.
            # if id_device in gantry.devices:
            # raise ValueError('Gantry server %s already has device id %d (stored ppk `%s`, given `%s`)' % (self.id, id_device, self.devices[id_device].ppk, ppk))
            # Device could be distributed over several gantries (detector loops, for example)
            self.gantry_devices[id_device].append(gantry)
        # Add a sub-device object
        sub_device = device.add_sub_device(id_sub_device, id_type, prefix)
        # self.state[device][sub_device] = ''
        #self.prefixes[device] = prefix
        #self.ppks[device][sub_device] = ppk
        #self.devices = self.state.keys()
        #self.devices.sort()
        return sub_device

    def process_xml_commands(self, gantry_xml_node):
        """Process a portion of XML command batch sent from the controller"""
        # The `id` attribute contains gantry server name
        for device_node in gantry_xml_node:
            if device_node.tag != 'device':
                raise ValueError('Expected <device> tag, got <%s>' % device_node.tag)
            id_device = int(device_node.attrib['id'])
            for sub_device_node in device_node:
                if sub_device_node.tag != 'subdevice':
                    raise ValueError('Expected <subdevice> tag, got <%s>' % sub_device_node.tag)
                id_sub_device = int(sub_device_node.attrib['id'])
                # Device may span several gantries. We assume that a sub-device is local to the given gantry.
                sub_device = self.locate_sub_device(id_device,id_sub_device)
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
                    message_id = int(symbol_node.text)
                    sub_device.set_message_id(message_id)
                else:
                    raise ValueError('Expected <command> tag, got <%s>' % command_node.tag)

    def process_command(self, command):
        """Process a binary command specified as tuple"""
        id_device, id_sub_device, id_message, validity = command
        # Device may span several gantries. We assume that a sub-device is local to the given gantry.
        sub_device = self.locate_sub_device(id_device,id_sub_device)
        sub_device.set_message_id(id_message)

    def get_gantry_messages(self):
        """Return a list of messages for all gantries that are managed by this gantry server.

        Gantries are identified by their numeric codes in the format `dyyyy` that should correspond
        to the numeric part of the gantry name {typically 'Pdyyyy'). In this convention `d`
        denotes the direction (d=0 is right-hand in the direction of growing stationing of the
        intfrastructure, d=1 is left-hand, `yyyy` is the stationing of the element in hundreds of
        meters)."""
        gantry_messages = {}
        for id_gantry in self.gantries:
            text = ""
            gantry = self.gantries[id_gantry]
            for id_device in gantry.get_device_id_list():
                device = gantry.get_device(id_device)
                for id_sub_device in device.get_sub_device_id_list():
                    sub_device = device.get_sub_device(id_sub_device)
                    # Sub-devices may be also detectors and other things that do not display
                    # messages on the gantry
                    if sub_device.has_message_text:
                        text += "%s/%s - %s\n" % (sub_device.get_prefix(), device.ppk, sub_device.get_message_text())
            gantry_messages[id_gantry] = text
        return gantry_messages


    def get_speed_limits(self):
        """Return actual speed limit data.

        The returned dictionary is indexed by gantry ids. Every dictionary element is a list of speed limit
        data that is applicable to devices of that particular gantry. Every list element is a tuple containing
        a sign id, lane it occupies, speed limit in kmph and vehicle class it should be applied to (0 for all
        vehicles."""
        speed_limits = defaultdict(list)
        for id_gantry in self.gantries:
            gantry = self.gantries[id_gantry]
            for id_device in gantry.get_device_id_list():
                device = gantry.get_device(id_device)
                for id_sub_device in device.get_sub_device_id_list():
                    sub_device = device.get_sub_device(id_sub_device)
                    # Sub-devices are of different type, we are explicitly interested in speed limits here.
                    if isinstance(sub_device, GantrySpeedLimit):
                        speed_limits[id_gantry].append(sub_device.get_speed_limit())
        return speed_limits


    def get_lane_closures(self):
        """Return a list of lane closures.

        The returned dictionary is indexed by gantry ids. Every dictionary element is a list of speed limit
        data that is applicable to devices of that particular gantry. Every list element is a tuple containing
        a sign id, lane it occupies, speed limit in kmph and vehicle class it should be applied to (0 for all
        vehicles."""
        lane_closures = defaultdict(list)
        for id_gantry in self.gantries:
            gantry = self.gantries[id_gantry]
            for id_device in gantry.get_device_id_list():
                device = gantry.get_device(id_device)
                for id_sub_device in device.get_sub_device_id_list():
                    sub_device = device.get_sub_device(id_sub_device)
                    # Sub-devices are of different type, we are explicitly interested in speed limits here.
                    if isinstance(sub_device, GantryRegulatorySign):
                        closure_info = sub_device.get_lane_closure()
                        if closure_info:
                            lane_closures[id_gantry].append(closure_info)
        return lane_closures


    def get_gantry_labels(self):
        """Return a list of gantry names for the current gantry server"""
        return self.gantries.keys()

    def __str__(self):
        """Turn the internal state information into a human-readable string"""
        ret = ""
        for id_gantry in self.gantries:
            gantry = self.gantries[id_gantry]
            dret = ""
            for id_device in gantry.get_device_id_list():
                device = gantry.get_device(id_device)
                sret = ""
                for id_sub_device in device.get_sub_device_id_list():
                    sub_device = device.get_sub_device(id_sub_device)
                    # Sub-devices may be also detectors and other things that do not display
                    # messages on the gantry
                    if sub_device.has_message_text:
                        if sret:
                            sret += ', '
                        sret += "%d/%s - " % (sub_device.id, sub_device.prefix)
                        sret += sub_device.get_message_text()
                if dret:
                    dret += ', '
                dret += "%d/%s {%s}" % (device.id, device.ppk, sret)
            if ret:
                ret += ', '
            ret += "%s {%s}" % (gantry.id, dret)
        return self.id + ': ' + ret


if __name__ == "__main__":
    tree = Et.parse('sokp.xml')
    root = tree.getroot()
    print "The root erlement of the file is " + repr(root)

    gantries = {}
    gantry_ld_map = {}
    for gantry_node in root:
        print gantry_node.tag, gantry_node.attrib
        id_gantry = gantry_node.attrib['id']
        gantry_server = GantryServer(id_gantry)
        for device in gantry_node:
            print ' ', device.tag, device.attrib
            id_device = int(device.attrib['id'])
            ppk = device.attrib['ppk']
            for sub_device in device:
                print '   ', sub_device.tag, sub_device.attrib
                id_sub_device = int(sub_device.attrib['id'])
                id_type = sub_device.attrib['type']
                prefix = sub_device.attrib['prefix']
                sub_instance = gantry_server.add_sub_device(id_device, ppk, id_sub_device, id_type, prefix)
                # We need a mapping from detector id to gantry, device, subdevice
                if isinstance(sub_instance, GantryLoopDetector):
                    for loop_detector in sub_device:
                        print '       ', loop_detector.tag, loop_detector.attrib
                        id_lane = int(loop_detector.attrib['id'])
                        position = loop_detector.attrib['position']
                        prefix = loop_detector.attrib['prefix']
                        gantry_ld_map[prefix] = (id_gantry, id_device, id_sub_device, id_lane, position, prefix)
        gantries[id_gantry] = gantry_server
        print gantry_server.get_gantry_messages()

    print gantry_ld_map
    print str(gantries)

    print gantries['R01-R-MX20017'].get_gantry_messages()

    # This is a template for a GantryInterface function for processing commands
    tree = Et.parse('gantry_command.xml')
    root = tree.getroot()
    for gantry_node in root:
        id_gantry = gantry_node.attrib['id']
        gantry_server = None
        try:
            gantry_server = gantries[id_gantry]
        except KeyError as e:
            print 'ERROR: Got command for non-existing gantry server '+id_gantry
        if gantry_server:
            gantry_server.process_xml_commands(gantry_node)

    print gantries['R01-R-MX20017'].get_gantry_messages()
    print gantries['R01-R-MX20017'].get_gantry_labels()
    print gantries['R01-R-MX20017'].get_speed_limits()

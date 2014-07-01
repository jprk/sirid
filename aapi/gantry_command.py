#!/usr/bin/python
# -*- coding: windows-1250 -*-

import xml.etree.ElementTree as Et
import pickle

def process_gantry_server_commands(tree):
    """Process a XML command batch sent from the controller"""

    root = tree.getroot()

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
                    command = (id_gantry_server, id_device, id_sub_device, id_message, validity)
                    print pickle.dumps(command,pickle.HIGHEST_PROTOCOL)
                else:
                    raise ValueError('Expected <command> tag, got <%s>' % command_node.tag)

if __name__ == "__main__":
    tree = Et.parse('gantry_command.xml')
    process_gantry_server_commands(tree)

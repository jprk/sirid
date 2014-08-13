#!/usr/bin/python
# -*- coding: utf-8 -*-

import openpyxl as px
from lxml import etree
from collections import defaultdict

wb = px.load_workbook('prirazeni_pdz+det.xlsx', use_iterators = True)
sh = wb.get_sheet_names()

gantryDict = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:defaultdict(list))))

for sheet in sh :
    p = wb.get_sheet_by_name ( sheet )
    if p :
        print '-- Sheet `{:s}`'.format(sheet)
        print '   p =',p
        pdim = 'A2:' + p.calculate_dimension().split(':')[1]
        # pdim = p.calculate_dimension()
        print '   dimension string `{:s}`'.format(pdim)
        print type(pdim)
        for row in p.iter_rows ( pdim ):
            # print row[0].value,row[0].internal_value,row[1].value,row[1].internal_value
            # For older openpyxl versions:
            # gantryId = row[0].internal_value
            # deviceId = int(row[6].internal_value)
            # subdevId = int(row[7].internal_value)
            # For openpyxl 2.0.4
            gantryId = row[0].value
            prefix   = row[5].value # this is used to distinguish loop detectors
            deviceId = int(row[6].value)
            subdevId = int(row[7].value)
            # I should probably not use lists, but ...
            subdev = []
            for k in row[1:6]:
                subdev.append ( k.value )
            gantryDict[gantryId][deviceId][subdevId][prefix] = subdev
    else :
        raise ValueError ( 'XLSX sheet `{:s} does not exist'.format ( sheet ))
        
# print gantryDict
# print stationing

gantries = gantryDict.keys()
gantries.sort()

root = etree.Element('root')
for gantryId in gantries :
    # Create a <gantry> element
    gantry = etree.SubElement ( root, 'gantry' )
    # Add attributes
    gantry.set ( 'id', gantryId )
    # Every gantry has got devices
    deviceDict = gantryDict[gantryId]
    devices = deviceDict.keys()
    devices.sort()
    for deviceId in devices :
        # Create a <device> element
        device = etree.SubElement ( gantry, 'device' )
        # Add attributes
        device.set ( 'id', str(deviceId) )
        #
        stationing = "0.0"
        position   = ''
        ppk        = ''
        prefix     = ''
        # Every device has got subdevices
        subdevDict = deviceDict[deviceId]
        subdevs = subdevDict.keys()
        subdevs.sort()
        for subdevId in subdevs :
            # A subdevice may have several nodes with different node ids (prefixes)
            subData = subdevDict[subdevId]
            nodes = subData.keys()
            nodes.sort()
            for nodeId in nodes:
                nodeData = subData[nodeId]
                # Create a <subdevice> element
                subdev = etree.SubElement ( device, 'subdevice' )
                # Add attributes
                subdev.set ( 'id', str(subdevId) )
                stype = nodeData[0]
                if not stype : stype = '?'
                subdev.set ( 'type', stype )
                # Every subdevice has at leat one <aimsunid> element
                aimsunid = etree.SubElement ( subdev, 'aimsunid' )
                aimsunid.text = '-1'
                # Some attributes of subdevice are in fact attributes of device
                if subData[1] : stationing = nodeData[1]
                if subData[2] : position   = nodeData[2]
                ppk    = nodeData[3]
                prefix = nodeData[4]
                if not prefix : prefix = '?'
                subdev.set ( 'prefix', prefix )
        # Check that we have a meaningful set of attributes
        if not ppk : ppk = '?'
        # Add device attributes that were stored with subdevices
        device.set ( 'stationing', str(stationing) )
        device.set ( 'position', position )
        device.set ( 'ppk', ppk )

# save it
tree = etree.ElementTree ( root )
tree.write ( "sokp.xml", encoding='utf-8', pretty_print=True, xml_declaration=True )



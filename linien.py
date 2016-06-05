#!/usr/bin/env python3

import urllib.request
import argparse
import sys
import xml.etree.ElementTree as etree

def is_int(s):
    try:
        int(s)
    except Exception:
        return False
    
    return True

def do_api_call(station):
    url = 'http://app.vrr.de/vrr/XSLT_DM_REQUEST?'
    url += 'outputFormat=XML&'
    url += 'language=de&'
    url += 'stateless=1&'
    url += 'coordOutputFormat=WGS84&'
    url += 'type_dm=stop&'
    url += 'name_dm=' + str(station) + '&'
    url += 'useRealtime=1&'
    url += 'mode=direct&'
    url += 'ptOptionsActive=1&'
    url += 'deleteAssignedStops_dm=1&'
    url += 'mergeDep=1&'
    url += 'limit=250'

    try:
        with urllib.request.urlopen(url) as response:
            xml = etree.fromstring(response.read())
            tree_lines = xml.findall(
                'itdDepartureMonitorRequest/itdServingLines/itdServingLine')
            tree_odv_name = xml.find('itdDepartureMonitorRequest/itdOdv')
    except Exception:
        print('Could not fetch xml')

    try:
        sstation = tree_odv_name.find('itdOdvName/odvNameElem').text
        splace = tree_odv_name.find('itdOdvPlace/odvPlaceElem').text
    except Exception:
        print('Could not interpret xml: station')
    
    print("Station: " + sstation + ', ' + splace)
    
    lines = []
    max = (0,0,0,0)
    
    for i in tree_lines:
        operator = ''
        try:
            leaf_diva = i.find('motDivaParams')
            operator = i.find('itdOperator/name').text
        except Exception:
            print('Could not interpred xml: line')


        line = i.attrib.get('number')
        direction_code = leaf_diva.attrib.get('direction')
        direction = i.attrib.get('direction')

        
        if (line is not None and direction is not None and direction_code is not None):
            lines.append((operator, line, direction, direction_code))
            max = (max[0] if max[0] > len(operator) else len(operator),
            max[1] if max[1] > len(line) else len(line),
            max[2] if max[2] > len(direction) else len(direction),
            max[3] if max[3] > len(direction_code) else len(direction_code)) 
            #print('{:<25} {:<10} {:<30} {:}'.format(operator, line, direction, direction_code))

    form = '{:<' + str(max[0]) + '} | {:<' + str(max[1]) + '} | {:<' + str(max[2]) + '} | {:<' + str(max[3]) + '}'
    print(form.format('Operator', 'Line', 'Direction', ''))
    
    for i in lines:
        print(form.format(i[0], i[1], i[2], i[3]))
        

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    if not is_int(sys.argv[1]):
        sys.exit(2)
    
    do_api_call(sys.argv[1])


if __name__ == '__main__':
    main()

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

def do_api_call(station, line, direction, warn, crit):
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
    url += 'limit=10'

    try:
        with urllib.request.urlopen(url) as response:
            xml = etree.fromstring(response.read())
            tree_deps = xml.findall(
                'itdDepartureMonitorRequest/itdDepartureList/itdDeparture')
            tree_odv_name = xml.find('itdDepartureMonitorRequest/itdOdv/itdOdvName')
    except Exception:
        return 'UNKNOWN - Could not fetch xml'

    if tree_odv_name.attrib.get('state') == 'notidentified':
        return 'UNKNOWN - Invalid station id.'
    else:
        try:
            sstation = tree_odv_name.find('odvNameElem').text
        except Exception:
            return 'UNKNOWN - Could not interpret xml: station'
            
    for i in tree_deps:
        try:
            leaf_line = i.find('itdServingLine')
            leaf_delay = leaf_line.find('itdNoTrain')
            leaf_mota_params = leaf_line.find('motDivaParams')
        except Exception:
            return 'UNKNOWN - Could not interpred xml: departure '


        sline = leaf_line.attrib.get('number')
        delay = leaf_delay.attrib.get('delay')
        sdirection = leaf_line.attrib.get('direction')
        sdirection_code = leaf_mota_params.attrib.get('direction')
        

        if not is_int(delay) and delay is not None:
            return 'UNKNOWN - Could not interpret delay: ' + str(delay)

        if (line is not None and delay is not None and
                sdirection is not None and sdirection_code is not None):
            if sline == line and direction == sdirection_code:
                severity = 'UNKOWN' # Default
                if int(delay) >= crit:
                    severity = 'CRITICAL'
                elif int(delay) >= warn:
                    severity = 'WARNING'
                else:
                    severity = 'OK'
                
                return severity + ' - ' + sline + ' -> "' + sdirection + '" ('  + sdirection_code + '): ' + delay + ' min | delay=' + str(delay)


    return 'UNKNOWN - Did not find any delay info of ' + str(line) + ' direction (' + str(direction) + ') on station "' + str(sstation) + '" (' + str(station) + ')'
    

def main():
    # line = '635'
    # station = '20011254' #Worringer
    # direction = 'R'
        
    parser = argparse.ArgumentParser()
    parser.add_argument('station', type=int, help='Public transport station id (A unique number, not its name!)')
    parser.add_argument('line', type=str, help='Public transport line number')
    parser.add_argument('direction', type=str, help='Direction of the line. "R" or "H"', choices=('R','H'))

    parser.add_argument('-w', '--warning', type=int, help='WARNING time limit in minutes', required=False, default=5)
    parser.add_argument('-c', '--critical', type=int, help='CRITICAL time limit in minutes', required=False, default=8)

    args = parser.parse_args()

    line = args.line
    station = args.station
    direction = args.direction
    warn = args.warning
    crit = args.critical

    result = do_api_call(station, line, direction, warn, crit)
    returncode = 3

    if result.startswith('UNKNOW'):
        returncode = 3
    elif result.startswith('CRITICAL'):
        returncode = 2
    elif result.startswith('WARNING'):
        returncode = 1
    elif result.startswith('OK'):
        returncode = 0
    else:
        returncode = 3
        result = 'UNKNOWN - Internal plugin error: Unknown return: \n"' + result + '"'

    print(result)
    sys.exit(returncode)

if __name__ == '__main__':
    main()

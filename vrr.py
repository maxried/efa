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
            leaf_notrain = leaf_line.find('itdNoTrain')
            leaf_mota_params = leaf_line.find('motDivaParams')
            leaf_datetime = i.find('itdDateTime')
            leaf_datetime_date = leaf_datetime.find('itdDate')
            leaf_datetime_time = leaf_datetime.find('itdTime')
        except Exception:
            return 'UNKNOWN - Could not interpred xml: departure '


        sline = leaf_line.attrib.get('number')
        delay = leaf_notrain.attrib.get('delay')
        sdirection = leaf_line.attrib.get('direction')
        sdirection_code = leaf_mota_params.attrib.get('direction')
        sdate = 'no date'

        dt = (leaf_datetime_date.attrib.get('year'),
              leaf_datetime_date.attrib.get('month'),
              leaf_datetime_date.attrib.get('day'),
              leaf_datetime_time.attrib.get('hour'),
              leaf_datetime_time.attrib.get('minute'))  
        
        if (is_int(dt[0]) and is_int(dt[1]) and is_int(dt[2]) and 
            is_int(dt[3]) and is_int(dt[4])):
            sdate = '{:04d}-{:02}-{:02} at {:02}:{:02}'.format(int(dt[0]), int(dt[1]), int(dt[2]), int(dt[3]), int(dt[4]))

        if not is_int(delay) and delay is not None:
            return 'UNKNOWN - Could not interpret delay: ' + str(delay)

        if (line is not None and delay is not None and
                sdirection is not None and sdirection_code is not None):
            if sline == line and direction == sdirection_code:
                delay = int(delay)
                severity = 'UNKOWN' # Default
                if delay >= crit:
                    severity = 'CRITICAL'
                elif delay >= warn:
                    severity = 'WARNING'
                else:
                    severity = 'OK'


                if delay == 0:
                    return (severity + ' - ' + sline + ' -> "' + sdirection + ': ' + sdate + ' (in time) | delay=0s\n' +
                            'Summary:\nLine ' + sline + ', direction "' + sdirection + '", is in time at stop "' + sstation + '". The scheduled departure is ' + sdate + '.')
                else:
                    return (severity + ' - ' + sline + ' -> "' + sdirection + ': ' + sdate + ' (delayed by ' + str(delay) + ' min) | delay=' +  str(delay * 60) + 's\n' +
                            'Summary:\nLine ' + sline + ', direction "' + sdirection + '", is late by ' + str(delay) + ' minutes on stop "' + sstation + '". Its scheduled departured was ' + sdate + '.')

                

    return 'OK - Did not find any delay info of ' + str(line) + ' direction (' + str(direction) + ') on station "' + str(sstation) + '" (' + str(station) + ')'
    

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

#!/usr/bin/env python3

import urllib.request
import urllib.parse
import sys
import xml.etree.ElementTree as etree

def main():
    stationname = urllib.parse.quote(sys.argv[1])
    xml = ""

    with urllib.request.urlopen('http://app.vrr.de/vrr/XML_STOPFINDER_REQUEST?outputFormat=XML&language=de&stateless=1&coordOutputFormat=WGS84&locationServerActive=1&type_sf=any&name_sf=' + stationname + '&SpEncId=0&anyObjFilter_sf=126&reducedAnyPostcodeObjFilter_sf=64&reducedAnyTooManyObjFilter_sf=2&useHouseNumberList=true&anyMaxSizeHitList=500') as response:
        xml = response.read()

    
    tree = etree.fromstring(xml)
    deps = tree.findall("itdStopFinderRequest/itdOdv/itdOdvName/odvNameElem")
    
    
    for i in deps:
        print(i.attrib.get('id') + ": " + i.text)

        
if __name__ == "__main__":
    main()

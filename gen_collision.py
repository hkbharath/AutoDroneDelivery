import gpxpy
#import matplotlib.pyplot as plt
from xml.dom.minidom import parse
import xml.dom.minidom
#import haversine
import argparse
from math import radians, cos, sin, asin, sqrt
import geopy.distance
import xml.etree.cElementTree as ET
from numpy import savetxt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--t1', help='First task name', type=str)
    parser.add_argument('--t2', help='Second task name', type=str)
    
    args = parser.parse_args()

    if args.t1 is None:
        print("Please First task name")
        exit(1)

    if args.t2 is None:
        print("Please Second task name")
        exit(1)

    uv_values = []

    DOMTree_t1 = xml.dom.minidom.parse(args.t1 + "_gps.gpx")
    path_t1 = DOMTree_t1.documentElement.getElementsByTagName("trkpt")
    ele_f1 = open(args.t1 + "_elevation.txt", 'r')
    
    DOMTree_t2 = xml.dom.minidom.parse(args.t2 + "_gps.gpx")
    path_t2 = DOMTree_t2.documentElement.getElementsByTagName("trkpt")
    ele_f2 = open(args.t2 + "_elevation.txt", 'r')

    for t, pt in enumerate(path_t1):

        lat_p1 = path_t1[t].getAttribute("lat")
        lon_p1 = path_t2[t].getAttribute("lon")
        ele_p1 = ele_f1.readline()

        lat_p2 = path_t2[t].getAttribute("lat")
        lon_p2 = path_t2[t].getAttribute("lon")
        ele_p2 = ele_f2.readline()

        coords_1 = (float(lat_p1), float(lon_p1), float(ele_p1))
        coords_2 = (float(lat_p2), float(lon_p2), float(ele_p2))

        d = geopy.distance.distance(coords_1, coords_2).m

        if d <= 30.0:
            uv_values.append(1)
        else:
            uv_values.append(0)

    savetxt('%s_uv.txt'%(args.t1), uv_values,fmt='%d', delimiter='\n')
    savetxt('%s_uv.txt'%(args.t2), uv_values,fmt='%d', delimiter='\n')

if __name__ == "__main__":
    main()
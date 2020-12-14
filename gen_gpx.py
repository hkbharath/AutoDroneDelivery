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

speed = 50
max_height = 120
ad_time = 3 #assuming 3 sec ascent and 3 second descent

def path_gen(l_start, l_stop, t):
    
    ele = []
    pos = []

    dh = max_height/ad_time

    ti = 0
    height = 0
    
    pos.append(l_start)
    ele.append(height)

    #Elevate
    for i in range(ad_time):
        height = height + dh
        pos.append(l_start)
        ele.append(height)
        ti = ti + 1
    
    height = max_height

    # movement path in straight line    
    #get line equation
    d_lat = (l_stop[0] - l_start[0])/(t - 2 * ad_time)
    m = (l_stop[1] - l_start[1])/(l_stop[0] - l_start[0])
    b = l_start[1] - m * l_start[0]
    
    n_lat = l_start[0]
    n_lon = l_start[1]

    while ti < (t - ad_time):
        n_lat = n_lat + d_lat
        n_lon = m * n_lat + b
        
        pos.append((n_lat, n_lon))
        ele.append(height)
        ti = ti + 1
    
    #Elevate in 3 seconds
    for i in range(ad_time):
        height = height - dh
        pos.append(l_stop)
        ele.append(height)

    return pos, ele        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-file', help='Where to look for the input file', type=str)
    args = parser.parse_args()
    if args.input_file is None:
        print("Please specify input file")
        exit(1)

    DOMTree = xml.dom.minidom.parse(args.input_file + ".gpx")
    #DOMTree2 = xml.dom.minidom.parse("backwordDrone.gpx")
    collection = DOMTree.documentElement
    #collection2 = DOMTree2.documentElement

    trkpts = collection.getElementsByTagName("trkpt")
    #trkpts2 = collection2.getElementsByTagName("trkpt")

    latti=trkpts[0].getAttribute("lat")
    longi=trkpts[0].getAttribute("lon")

    latti2=trkpts[-1].getAttribute("lat")
    longi2=trkpts[-1].getAttribute("lon")

    #print(str(latti)+" "+str(longi)+" "+str(latti2)+" "+str(longi2))

    coords_1 = (float(latti), float(longi))
    coords_2 = (float(latti2), float(longi2))

    d=geopy.distance.distance(coords_1, coords_2).km

    t=(d/speed)*60*60
    gps_values, ele_values = path_gen(coords_1,coords_2,t)
    
    GPX = ET.Element("gpx",xmlns="http://www.topografix.com/GPX/1/1",xsi="http://www.w3.org/2001/XMLSchema-instance",schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" ,version="1.1", creator="OpenRouteService.org")
    mt = ET.SubElement(GPX, "metadata")
    trk= ET.SubElement(GPX, "trk")
    ET.SubElement(trk, "name").text = "Output"
    ET.SubElement(trk, "desc").text = "Output"
    trkseg= ET.SubElement(trk, "trkseg")
    for x in gps_values: 
        ET.SubElement(trkseg, "trkpt",lat=str(x[0]),lon=str(x[1]))
    tree = ET.ElementTree(GPX)
    tree.write("%s_gps.gpx"%(args.input_file))

    savetxt('%s_elevation.txt'%(args.input_file), ele_values,fmt='%f', delimiter='\n')

if __name__ == "__main__":
    main()
from numpy.random import randint
import gpxpy
import random
import numpy as np

from numpy import asarray
from numpy import savetxt

from xml.dom.minidom import parse
import xml.dom.minidom
#import haversine
import argparse
from math import radians, cos, sin, asin, sqrt
import geopy.distance
import xml.etree.cElementTree as ET


speed = 50

def signalSim(t):
    low_n = randint(1, t/4)
    mid_n = randint(1, t/4)
    high_n = t - low_n - mid_n
    
    hig_sig = randint(95,100, high_n)
    mid_sig = randint(70,95, mid_n)
    low_sig = randint(50,70, low_n)

    final_sig = np.concatenate((hig_sig, mid_sig, low_sig))
    
    random.shuffle(final_sig)
    
    return final_sig

def batteryDrain(t):
    
    #irand=random.sample(range(1, 100),t)
    irand = randint(70,100, t)
    irand.sort()
    return irand[::-1]

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

    coords_1 = (float(latti), float(longi))
    coords_2 = (float(latti2), float(longi2))

    d=geopy.distance.distance(coords_1, coords_2).km
    t=(d/speed)*60*60 + 2 # +2 to add extra simulation for start and end
    
    sig_values = signalSim(int(t))
    savetxt('%s_signal.txt'%(args.input_file),sig_values,fmt='%d', delimiter='\n')
    
    values_battery = batteryDrain(int(t))
    savetxt('%s_batterydrain.txt'%(args.input_file),values_battery,fmt='%d',delimiter='\n')

if __name__ == "__main__":
    main()
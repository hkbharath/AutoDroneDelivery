from numpy.random import randint
import gpxpy
import random
import numpy as np

from numpy import asarray
from numpy import savetxt

from xml.dom.minidom import parse
import xml.dom.minidom
import haversine
import argparse
from math import radians, cos, sin, asin, sqrt
import geopy.distance
import xml.etree.cElementTree as ET


def signalHigh(t):
    n=int(t/2)
    
    irand1 = randint(70,95,n)
    irand2 = randint(95,100,n)
    irand = np.concatenate((irand1,irand2))
    
    random.shuffle(irand)
    
    return irand
    



def signalLow(t):
    irand1 = randint(50,70,t)
    return irand1


def batteryDrain(t):
    
    irand=random.sample(range(1, 100),t)
    irand.sort(reverse=True)
    return irand






def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-file', help='Where to look for the input file', type=str)
    args = parser.parse_args()
    if args.input_file is None:
        print("Please specify input file")
        exit(1)

    DOMTree = xml.dom.minidom.parse(args.input_file)
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
    t=(d/50)*60*60
    
    values_high=signalHigh(int(t))
    savetxt('high.txt',values_high,fmt='%d', delimiter=',')
    values_low=signalLow(int(t))
    savetxt('low.txt',values_low,fmt='%d',delimiter=',')
    values_battery=batteryDrain(int(t))
    savetxt('batterydrain.txt',values_battery,fmt='%d',delimiter=',')

    

if __name__ == "__main__":
    main()
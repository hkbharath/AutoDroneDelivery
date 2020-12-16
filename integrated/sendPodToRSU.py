from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import sched,time
import os
import threading
from geopy.distance import geodesic
import socket
from datetime import datetime, timedelta
import json

pnconfig = PNConfiguration()
pnconfig.publish_key = 'pub-c-cbac1ba8-84b2-469d-a59b-7d66d9b4cb2a'
pnconfig.subscribe_key = 'sub-c-88b6488e-3adb-11eb-b6eb-96faa39b9528'
pnconfig.ssl = True
pubnub = PubNub(pnconfig) 

class PostAccidentSignalData:
    def __init__(self, rsuId, accidentLongitude, accidentLatitude, accidentVehicleId):
        self.rsuId = rsuId
        self.accidentLongitude = accidentLongitude
        self.accidentLatitude = accidentLatitude
        self.accidentVehicleId = accidentVehicleId

def my_publish_callback(envelope, status):
   # Check whether request successfully completed or not
    if not status.is_error():
        pass
class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass
    def status(self, pubnub, status):
        pass
    def message(self, pubnub, message):
        if message.message == None:
            print("")
        else:
            print("From RSU-4 : ",message.message)
            continue_moving(message.message)

accidentSignalData1 = PostAccidentSignalData("X", "Vehicle-11", "-6.254735", "53.343639")

def sendToPod1RSU():
    print("connected")
    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels("RSU-4").execute()
    pubnub.publish().channel("RSU-4").message({
      "rsuId": accidentSignalData1.rsuId,
      "accidentVehicleId": accidentSignalData1.accidentVehicleId,
      "accidentLongitude": accidentSignalData1.accidentLongitude,
      "accidentLatitude": accidentSignalData1.accidentLatitude
    }).pn_async(my_publish_callback)
    pubnub.unsubscribe().channels("RSU-4").execute()
	
sendToPod1RSU()
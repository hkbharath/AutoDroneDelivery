import socket
import _thread
from random import seed
from random import randint
import functools
import time
from ctypes import *

class Payload(Structure):
    _fields_ = [("X", c_uint32),
                ("Y", c_uint32),
                ("Z", c_uint32),
                ("Port", c_uint32),
                ("Type",c_uint32),
                ("Near",c_uint32),
                ("Drone_id", c_uint32),
                ("Direction", c_uint32),
                ("Deviation", c_uint32)]
           
                

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
drone_2=5007
drone_3=5006
MESSAGE = "X:2,Y:2,Z:2"
my_cords=[2,2,2]
mm=MESSAGE.encode()
print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

 

#sock = socket.socket(socket.AF_INET, # Internet
#                    socket.SOCK_DGRAM) # UDP
#sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

def send(s):
  print("hiii")
  while True: 
    value = randint(0, 1000)
    if(value<1):
      print('hiiiiiiiiiiiiiiiiii')
      sock_1 = socket.socket(socket.AF_INET, # Internet
                           socket.SOCK_DGRAM) # UDP
      payload_out = Payload(2, 2, 2,5005,1,4,0,0,0)
      sock_1.sendto(payload_out, (UDP_IP, drone_2))
      sock_1.sendto(payload_out,(UDP_IP, drone_3))
      break
   
def rec(s):
  while(True):
    buff= sock.recv(sizeof(Payload)) # buffer size is 1024 bytes
    payload_in = Payload.from_buffer_copy(buff)
    
    if(payload_in.Type==1):
      rec_cords=[payload_in.X,payload_in.Y,payload_in.Z]
      print(rec_cords)
      if functools.reduce(lambda x, y : x and y, map(lambda p, q: p == q,my_cords,rec_cords), True): 
       
         pp=Payload(2, 2, 2,5005,2,1,0,0,0)
         sock.sendto(pp,(UDP_IP,payload_in.Port))
      else: 
         pp=Payload(2, 2, 2,5005,2,0,0,0,0)
         sock.sendto(pp,(UDP_IP,payload_in.Port))
      print("received message: ")
    if(payload_in.Type==2):
      if(payload_in.Near==1):
        st=str(payload_in.Port)+" is near and deviation packet is send"
        print(st)
        sock_1 = socket.socket(socket.AF_INET, # Internet
                           socket.SOCK_DGRAM) # UDP
        pp=Payload(2, 2, 2,5005,2,0,0,1,10)
        sock_1.sendto(pp, (UDP_IP, drone_2))
        sock_1.sendto(pp,(UDP_IP, drone_3))
        
      else :
        st=str(payload_in.Port)+" is far"
        print(st)
        
        
def rec1(s):
  while(True):
    buff= sock.recv(sizeof(Payload)) # buffer size is 1024 bytes
    payload_in = Payload.from_buffer_copy(buff)
    
    if(payload_in.Type==1):
      rec_cords=[payload_in.X,payload_in.Y,payload_in.Z]
      print(rec_cords)
      if functools.reduce(lambda x, y : x and y, map(lambda p, q: p == q,my_cords,rec_cords), True): 
       
         pp=Payload(2, 2, 2,5005,2,1,0,0,0)
         sock.sendto(pp,(UDP_IP,payload_in.Port))
      else: 
         pp=Payload(2, 2, 2,5005,2,0,0,0,0)
         sock.sendto(pp,(UDP_IP,payload_in.Port))
      print("received message: ")
    if(payload_in.Type==2):
      if(payload_in.Near==1):
        st=str(payload_in.Port)+" is near and deviation packet is send"
        print(st)
        sock_1 = socket.socket(socket.AF_INET, # Internet
                           socket.SOCK_DGRAM) # UDP
        pp=Payload(2, 2, 2,5005,2,0,0,1,10)
        sock_1.sendto(pp, (UDP_IP, drone_2))
        sock_1.sendto(pp,(UDP_IP, drone_3))
        
      else :
        st=str(payload_in.Port)+" is far"
        print(st)

_thread.start_new_thread( send, ("1", ) )
_thread.start_new_thread( rec, ("2", ) )
_thread.start_new_thread( rec1, ("3", ) )

 

while 1:
   pass
    

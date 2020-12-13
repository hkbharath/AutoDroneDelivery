import socket
from ctypes import *


class Payload(Structure):
    _fields_ = [("ptype",c_uint32),
                ("lat", c_float),
                ("long", c_float),
                ("height", c_float),
                ("battery_power", c_uint32),
                ("obstacle",c_bool),
                ("sig_str",c_uint32)]

port = 33300
server = socket.gethostbyname(socket.gethostname())
addr = (server, port)
# Create a client socket
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect(addr)


# Send data to server
def send(msg):
    #data = "Hello Server!"
    #clientSocket.send(data.encode())
    clientSocket.send(msg)
    data_from_server = clientSocket.recv(1024)
    print(data_from_server.decode())


payload_out = Payload(1, 10.5, 20.5, 120.0, 10, True, 6)
send(payload_out)
# close the connection
clientSocket.close()

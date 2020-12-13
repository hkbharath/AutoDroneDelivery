import socket
import threading
from ctypes import *


class Payload(Structure):
    _fields_ = [("ptype",c_uint32),
                ("lat", c_float),
                ("long", c_float),
                ("height", c_float),
                ("battery_power", c_uint32),
                ("obstacle",c_bool),
                ("sig_str",c_uint32)]


# define the port on which you want to connect
port = 33300
serv_host = socket.gethostname()
server = socket.gethostbyname(serv_host)
addr = (server, port)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(addr)


def handle_client(conn, address):
    print("Got connected to ", address)

    connected = True
    while connected:
        # buff = serverSocket.recv(1024)
        buff = conn.recv(sizeof(Payload))
        if len(buff) > 0:
            payload_in = Payload.from_buffer_copy(buff)
            print("Received latitude={}, longitude={}, height={}, battery-power={}, obstacle={}, signal_strength={}.".format(payload_in.lat, payload_in.long,payload_in.height, payload_in.battery_power,payload_in.obstacle,payload_in.sig_str))
            conn.send('Message received'.encode())




def start_server():
    serverSocket.listen()
    while True:
        conn, address = serverSocket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, address))
        thread.start()


print("socket has started listening...")
start_server()





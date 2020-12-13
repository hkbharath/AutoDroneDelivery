import argparse
import socket
import time
from numpy.random import randint
import random
import numpy as np
from payloads import *

###### Constant Configurations ######
reconnect_time = 120 # in sec
default_capacity = 5 # in kg
default_server_port = 33001
default_pos = (0.0,0.0)
avg_speed = 50 # km/h
ad_time = 3 #time taken for ascent and descent
max_height = 120 # in m
###### Constant Configurations ######

def get_simulation(dest_pos, task_id):
    # read a task file and follwo the task
    yield 0

def get_base_sever(position, server_config):
    return ("",0)

def activate(drone_id, init_pos, server=None, server_port=None, server_config=None):
    bl_addr = (server, server_port)

    if server is None:
        bl_addr = get_base_sever(init_pos, server_config)
    
    # Create a client socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(bl_addr)

    print("Successfully connected to server %s:%d"%(bl_addr[0], bl_addr[1]))

    # send init message
    drone_init = DroneConnect(drone_id, default_capacity, 100, False) # add batter strength model
    clientSocket.send(drone_init)

    # wait for ack
    buff = clientSocket.recv(sizeof(Ack))
    ack_ret = Ack.from_buffer_copy(buff)
    
    # retry later if connection is not accepted
    if ack_ret.is_accepted == False:
        time.sleep(reconnect_time)
        return init_pos
    
    print("Initialized communication to server %s:%d"%(bl_addr[0], bl_addr[1]))

    # wait for the next task
    dest_pos = None
    task_id = None
    while True:
        buff = clientSocket.recv(sizeof(BaseTask))
        task = BaseTask.from_buffer_copy(buff)

        if task.weight > default_capacity:
            # Reject the task
            clientSocket.send(Ack(False))
        else:
            # Accept the task
            task_id = task.task_id
            dest_pos = (task.dest_lat, task.dest_lon)
            clientSocket.send(Ack(True))
            break
    
    #start the task
    for sim in get_simulation(dest_pos, task_id):
        # sim is DroneUpdate
        clientSocket.send(sim)

    # close the connection
    clientSocket.close()

    return curr_pos


def main():

    #define the argumes required to be passed for starting the drone
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--drone-id', help='Assign a unique id for this drone', type=int)
    parser.add_argument('--server-config', help='Server Configuration file', type=str)
    parser.add_argument('--server', help='Base location server IP', type=str)
    parser.add_argument('--server-port', help='Base location server port', type=int)
    parser.add_argument('--position', help='Initial position', type=str)

    args = parser.parse_args()
    
    if args.drone_id is None :
        print("Provide --drone-id <ID>")
        exit(1)

    if args.server is None and args.server_config is None:
        print("Provide --server <IP> or --server-config <Server config file>")
        exit(1)

    if args.server_port is None:
        args.server_port = default_server_port
    
    if args.position is None:
        args.position = default_pos


if __name__ == "__main__":
    main()
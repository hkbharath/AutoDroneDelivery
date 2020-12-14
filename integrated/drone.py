import argparse
import socket
import time
import random
import os
import math
import geopy.distance
from payloads import *
from geopy.point import Point

###### Constant Configurations ######
reconnect_time = 120 # in sec
default_capacity = 5 # in kg
default_server = '127.0.0.1'
default_server_port = 33001
#default_pos = (53.343473, -6.251387)
default_pos = (53.309282, -6.223975)
avg_speed = 50 # km/h
ad_time = 3 #time taken for ascent and descent
max_height = 120 # in m
###### Constant Configurations ######

is_deviate = False

def get_bearing(l_start, l_stop):
    start_lat = math.radians(l_start[0])
    start_lng = math.radians(l_start[1])
    end_lat = math.radians(l_stop[0])
    end_lng = math.radians(l_stop[1])

    d_lng = end_lng - start_lng
    if abs(d_lng) > math.pi:
        if d_lng > 0.0:
            d_lng = -(2.0 * math.pi - d_lng)
        else:
            d_lng = (2.0 * math.pi + d_lng)

    tan_start = math.tan(start_lat / 2.0 + math.pi / 4.0)
    tan_end = math.tan(end_lat / 2.0 + math.pi / 4.0)
    d_phi = math.log(tan_end / tan_start)
    bearing = (math.degrees(math.atan2(d_lng, d_phi)) + 360.0) % 360.0

    return bearing

def path_sim(l_start, l_stop):
    global is_deviate

    d = geopy.distance.distance(l_start, l_stop).km

    t = (d/avg_speed)*60*60
    # 0th position
    yield l_start

    #Elevate in 3 seconds
    ti = 0
    for i in range(ad_time):
        yield l_start
        ti = ti + 1
        
    # movement path in straight line    
    #get line equation
    d_lat = (l_stop[0] - l_start[0])/(t - 2 * ad_time)
    m = (l_stop[1] - l_start[1])/(l_stop[0] - l_start[0])
    b = l_start[1] - m * l_start[0]
    
    n_lat = l_start[0]
    n_lon = l_start[1]

    while ti < (t - ad_time):
        if is_deviate:
            #TODO : start thread to get bearing and distance of deviation
            is_deviate = False
            d = geopy.distance.distance(meters=10)
            c_bearing = get_bearing((l_start[0], l_start[1]), (n_lat, n_lon))

            finalp = d.destination(point=Point(n_lat, n_lon), bearing=c_bearing-90)

            n_lat = finalp.latitude
            n_lon = finalp.longitude

            #reset line equation
            d_lat = (l_stop[0] - n_lat)/(t - ad_time - ti)
            m = (l_stop[1] - n_lon)/(l_stop[0] - n_lat)
            b = n_lon - m * n_lat
            yield (n_lat, n_lon)
        else:
            n_lat = n_lat + d_lat
            n_lon = m * n_lat + b
            
            yield (n_lat, n_lon)
            ti = ti + 1

    #descent
    for i in range(ad_time):
        yield l_stop

def get_simulation(init_pos, dest_pos, task_id):
    global is_deviate
    # read sensors data
    bat_f = open(task_id + "_batterydrain.txt", "r")
    ele_f = open(task_id + "_elevation.txt", "r")
    sig_f = open(task_id + "_signal.txt", "r")
    uv_f = open(task_id + "_uv.txt", "r")
    
    gps_sim = path_sim(init_pos, dest_pos)

    is_conflict = False

    last_update = None

    for (lat, lon) in gps_sim:
        bat_v = int(bat_f.readline())
        ele_v = float(ele_f.readline())
        sig_v = int(sig_f.readline())
        uv_v = int(uv_f.readline())
        last_update = DroneUpdate(lat, lon, ele_v, bat_v, uv_v, sig_v, True, False)
        yield last_update
        if uv_v and not is_conflict:
            is_deviate = True
            is_conflict = True
            (lat, lon) = next(gps_sim)
            last_update = DroneUpdate(lat, lon, ele_v, bat_v, uv_v, sig_v, True, False)
            yield last_update
        # conflict stays till the uv_v resets.
        if is_conflict and not uv_v:
            is_conflict = False
    last_update.is_complete = True
    last_update.is_moving = False
    yield last_update

def get_base_sever(position, server_config):
    return (default_server, default_server_port)

def activate(drone_id, init_pos, server=None, server_port=None, sim_dir="../simulation"):
    bl_addr = (server, server_port)

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
            task_id = os.path.join(sim_dir, "task%d"%(task.task_id))
            dest_pos = (task.dest_lat, task.dest_lon)
            clientSocket.send(Ack(True))
            break
    
    print("Starting the task %s"%(task_id))
    #start the task
    for sim in get_simulation(init_pos, dest_pos, task_id):
        # sim is DroneUpdate
        clientSocket.send(sim)
    print("Completed the task %s"%(task_id))
    # close the connection
    clientSocket.close()

    # on successful completion return final position for reconnection
    return dest_pos


def main():

    init_pos = default_pos
    server = default_server
    server_port = default_server_port

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
    
    if args.position is not None:
        p = Point(args.position)
        init_pos = (p.latitude, p.longitude)

    while True:
        if args.server_config is not None:
            get_base_sever(init_pos, args.server_config)
            init_pos = activate(args.drone_id, init_pos, server=server, server_port=server_port)
        else:
            activate(args.drone_id, init_pos, server=server, server_port=server_port)
        break


if __name__ == "__main__":
    main()
import argparse
import socket
import time
import random
import os
import math
import json
import threading
from threading import Thread
import geopy.distance
from payloads import *
from geopy.point import Point

###### Constant Configurations ######
reconnect_time = 120 # in sec
default_capacity = 5 # in kg
default_server = '127.0.0.1'
default_server_port = 33001
default_pos = (53.343473, -6.251387)
avg_speed = 50 # km/h
ad_time = 3 #time taken for ascent and descent
max_height = 120 # in m
seperation = 30 # in m
bearing_dev = -90 # 90 to the left
server_config = 'server_setup.json'
simulation_dir = "../simulation"
###### Constant Configurations ######

is_deviate = False
conflict_pred = []

class PathController:
    def __init__(self, lat, lon, ele):
        self.lock = threading.Lock()
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.al_drone = 0
        self.init()

    def init(self):
        self.is_deviation = False
        self.dist = 0
        self.bearing = 0
        self.height = 0


    def set_deviation(self, dist, bearing, height):
        global conflict_pred
        self.lock.acquire()
        self.is_deviation = True
        self.dist = dist
        self.bearing = bearing
        self.height = height
        conflict_pred = []
        self.lock.release()
    
    def is_deviation_set(self):
        return self.is_deviation
    
    def get_deviation(self):
        (dist, bearing, height) = (self.dist, self.bearing, self.height)

        self.lock.acquire()
        # reset the deviation variables
        self.init()
        self.lock.release()

        return (dist, bearing, height)

    def get_gps(self):
        return (self.lat, self.lon, self.ele)
    
    def set_gps(self, lat, lon, ele):
        self.lock.acquire()
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.lock.release()

    def set_al_drone(self, drone_id):
        self.al_drone = drone_id
    
    def get_al_drone(self):
        return self.al_drone

p_controller = None

def get_travel_time(d):
    return (d/avg_speed)*60*60

def get_drone_conncetion(drone_id):
    with open(server_config) as sc:
        servers = json.load(sc)
        for drone in servers['drones']:
            if drone['id'] == drone_id:
                return (drone['ip'], drone['peer_port'])
    return None

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

def path_sim(l_start, l_stop, is_conflict_pred=False):
    global is_deviate

    d = geopy.distance.distance(l_start, l_stop).km

    t = get_travel_time(d)
    
    ti = 0

    if not is_conflict_pred:
        # 0th position
        yield l_start

        #Elevate in 3 seconds
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
        if not is_conflict_pred and p_controller.is_deviation_set():
            (dist, bearing, height) = p_controller.get_deviation()
            d = geopy.distance.distance(meters=dist)
            c_bearing = get_bearing((l_start[0], l_start[1]), (n_lat, n_lon))
            print("Taking deviation %d:%d"%(dist, bearing))
            finalp = d.destination(point=Point(n_lat, n_lon), bearing = c_bearing + bearing)

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
            Thread(target = acc_det(n_lat, n_lon)).start()
            
            yield (n_lat, n_lon)
            ti = ti + 1

    #descent
    for i in range(ad_time):
        yield l_stop

def uv_simulation():
    while True:
        if conflict_pred == None or len(conflict_pred) == 0:
            yield 0
        else:
            yield conflict_pred.pop(0)
                                
def acc_det(lat, lon):
    curr_pos = (float(lat), float(lon))
    acc_pos = (53.376988,-6.248487)
    d = geopy.distance.distance(curr_pos, acc_pos).m
    
    if d<4000 :
        import sendPodToRSU

def communicate_diversion():
    drone_id = p_controller.get_al_drone()
    p_addr  = get_drone_conncetion(drone_id)
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # try:
    # Create a client socket
    clientSocket.connect(p_addr)
    print("Successfully connected to drone %s:%d"%(p_addr[0], p_addr[1]))

    # send current location
    (lat, lon, ele) = p_controller.get_gps()
    payload = PeerPayload(lat, lon, ele, 0, 0, 0)
    clientSocket.send(payload)
    
    #receieve 
    buff = clientSocket.recv(sizeof(PeerPayload))
    payload = PeerPayload.from_buffer_copy(buff)
    if payload.Deviation != 0:
        print("Recieved deviation: ", payload.Deviation, payload.bearing)
        p_controller.set_deviation(payload.Deviation, payload.bearing, 0)
        return True
    # except Exception as e:
    #     print("Failed to connect to drone %s:%d"%(p_addr[0], p_addr[1]))
    #     clientSocket.close()
    return False

def get_simulation(init_pos, dest_pos, task_id):
    global is_deviate
    # read sensors data
    bat_f = open(task_id + "_batterydrain.txt", "r")
    ele_f = open(task_id + "_elevation.txt", "r")
    sig_f = open(task_id + "_signal.txt", "r")
    uv_sim = uv_simulation()
    gps_sim = path_sim(init_pos, dest_pos)

    is_conflict = False

    last_update = None

    for (lat, lon) in gps_sim:
        bat_v = int(bat_f.readline())
        ele_v = float(ele_f.readline())
        sig_v = int(sig_f.readline())
        uv_v = next(uv_sim)
        
        # update curr course
        p_controller.set_gps(lat, lon, ele_v)
        
        last_update = DroneUpdate(lat, lon, ele_v, bat_v, uv_v, sig_v, True, False)
        yield last_update

        if uv_v or p_controller.is_deviation_set():
            #get last alert drone and communicate the course
            if uv_v and not communicate_diversion():
                continue
            
            (lat, lon) = next(gps_sim)
            
            # update curr course
            p_controller.set_gps(lat, lon, ele_v)
            
            last_update = DroneUpdate(lat, lon, ele_v, bat_v, uv_v, sig_v, True, False)
            yield last_update

    last_update.is_complete = True
    last_update.is_moving = False
    yield last_update

def predict_collision(curr_pos, dest_pos):
    global conflict_pred

    preds = []
    d = geopy.distance.distance(curr_pos, dest_pos).km
    t = get_travel_time(d)

    my_gps = path_sim(curr_pos, dest_pos, is_conflict_pred=True)
    coll_gps = path_sim(dest_pos, curr_pos)
    for my_pos in my_gps:
        coll_pos = next(coll_gps)

        d = geopy.distance.distance(my_pos, coll_pos).m

        if d <= 2*seperation:
            preds.append(1)
        else:
            preds.append(0)
    
    conflict_pred = preds

def get_init_base_server(server_config, server_id):
    with open(server_config) as sc:
        servers = json.load(sc)
        for server in servers['base_servers']:
            if server['id'] == server_id:
                return (server['location']['lat'], server['location']['lon']), server['ip'], server['drone_port']
    return default_pos, default_server, default_server_port

def get_server_for_loc(server_config, init_pos):
    with open(server_config) as sc:
        servers = json.load(sc)
        for server in servers['base_servers']:
            if abs(server['location']['lat'] - init_pos[0]) < 10e-6 and abs(server['location']['lon'] - init_pos[1]) < 10e-6:
                return server['ip'], server['drone_port']
    return default_server, default_server_port

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

        #recieve alert if any
        buff = clientSocket.recv(sizeof(BaseUpdate))
        bupdate = BaseUpdate.from_buffer_copy(buff)
        if bupdate.is_alert:
            predict_collision((sim.lat, sim.lon), dest_pos)
            p_controller.set_al_drone(bupdate.al_drone_id)
        time.sleep(1)
    
    print("Completed the task %s"%(task_id))
    # close the connection
    clientSocket.close()

    # on successful completion return final position for reconnection
    return dest_pos

def start_peer_listener(server, port, drone_id):

    addr = (server, port)

    peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peerSocket.bind(addr)

    print("Starting peer listener on [{}] at port {}".format(server, port))
    # try:
    if True:
        peerSocket.listen()
        while True:
            conn, address = peerSocket.accept()
            # while True:
            buff = conn.recv(sizeof(PeerPayload))
            payload = PeerPayload.from_buffer_copy(buff)
            print("Receieved payload")
            curr_pos = p_controller.get_gps()

            dist = geopy.distance.distance(curr_pos, (payload.lat, payload.lon, payload.height)).m
            if dist <= seperation:
                p_controller.set_deviation(seperation, bearing_dev, 0)
                conn.send(PeerPayload(curr_pos[0], curr_pos[1], curr_pos[2], drone_id, bearing_dev, seperation))
                print("Sending deviation: ", curr_pos[0], curr_pos[1], curr_pos[2], drone_id, bearing_dev, seperation)
            else:
                conn.send(PeerPayload(curr_pos[0], curr_pos[1], curr_pos[2], drone_id, 0, 0))
                print("Sending gps: ", curr_pos[0], curr_pos[1], curr_pos[2], drone_id, 0, 0)
            conn.close()
    
    # except Exception as e:
    #     peerSocket.close()

def main():
    global server_config
    global p_controller

    init_pos = default_pos
    server = default_server
    server_port = default_server_port

    #define the argumes required to be passed for starting the drone
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--drone-id', help='Assign a unique id for this drone', type=int)
    parser.add_argument('--server-id', help='Assign a unique server id for this drone', type=int)
    parser.add_argument('--server-config', help='Server Configuration file', type=str)
    parser.add_argument('--simulation-dir', help="Specify the custom simulation directory", type=str)
    args = parser.parse_args()
    
    if args.drone_id is None :
        print("Provide --drone-id <ID>")
        exit(1)

    if args.server_config is None:
        print("Provide --server-config <Server config file>")
        exit(1)
    
    if args.server_id is None and args.server_config is not None:
        print("Provide --server_id <Server Id>")
        exit(1)

    if args.simulation_dir is not None:
        simulation_dir = args.simulation_dir

    server_config = args.server_config
    init_pos, server, server_port = get_init_base_server(args.server_config, args.server_id)
    peer_ip, peer_port = get_drone_conncetion(args.drone_id)

    p_controller = PathController(init_pos[0], init_pos[1], 0)

    #keep a peer listener open
    peer_thread = threading.Thread(target=start_peer_listener, args=(peer_ip, peer_port, args.drone_id))
    peer_thread.start()

    is_start = True
    while True:
        if args.server_config is not None and not is_start:
            server, server_port = get_server_for_loc(args.server_config, init_pos)
        init_pos = activate(args.drone_id, init_pos, server=server, server_port=server_port, sim_dir=simulation_dir)
        is_start = False
        #break


if __name__ == "__main__":
    main()

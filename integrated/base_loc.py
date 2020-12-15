import argparse
import socket
import time
import threading
import csv
import os
import datetime
import json

from payloads import *
import xml.etree.cElementTree as ET

###### Constant Configurations ######
task_wait_sleep_time = 10 # in sec
package_weight = 5 # in kg
default_port = 33001
default_dest1 = (53.309282, -6.223975)
default_dest2 = (53.343473, -6.251387)
record_path = "../record"
server_config = None
###### Constant Configurations ######

class TaskQueue:
    #maintain task queue for each drone
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
    
    def add_task(self, base_task):
        self.lock.acquire()
        self.queue.append(base_task)
        self.lock.release()
    
    def task_exists(self):
        return len(self.queue) != 0
    
    def get_task(self):
        self.lock.acquire()
        return self.queue.pop(0)
        self.lock.release()

class ConflictMgr:
    #maintain task queue for each drone
    def __init__(self):
        self.drones = []
        self.lock = threading.Lock()
    
    def add_alert(self, dest_loc, drone_id):
        self.lock.acquire()
        for drone in self.drones:
            if drone['dest_loc'] == dest_loc:
                drone['alert'] = True
                drone['al_drone'] = drone_id
        self.lock.release()
    
    def get_alert(self, drone_id):
        for drone in self.drones:
            if drone['id'] == drone_id:
                if drone['alert']:
                    al_drone = drone['al_drone']
                    drone['alert'] = False
                    drone['al_drone'] = 0
                    return True, al_drone
                return drone['alert'], drone['al_drone']
    
    def add_drone(self, drone_id, dest_loc):        
        drone = {}
        #init Drone Values
        drone['id'] = drone_id
        drone['dest_loc'] = dest_loc
        drone['alert'] = False
        drone['al_drone'] = 0

        self.lock.acquire()
        self.drones.append(drone)
        self.lock.release()
    
    def remove_drone(self, drone_id):
        self.lock.acquire()
        for drone in self.drones:
            if drone['id'] == drone_id:
                self.drones.remove(drone)
                break
        self.lock.release()

# check if exit flag set to any drone
def is_exit(drone_id):
    return False

def writeGPXDom(rec_file, task_id, drone_id):
    
    gpx_root = ET.Element("gpx",
                        xmlns="http://www.topografix.com/GPX/1/1",
                        xsi="http://www.w3.org/2001/XMLSchema-instance",
                        schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
                        version="1.1", creator="OpenRouteService.org")
    trk = ET.SubElement(gpx_root, "trk")
    ET.SubElement(trk, "name").text = "Drone Track Trace"
    ET.SubElement(trk, "desc").text = "Stores the path on which the drone tarvelled"
    trkseg= ET.SubElement(trk, "trkseg")
    
    with open(rec_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            ET.SubElement(trkseg, "trkpt",lat = row[1], lon = row[2])
    tree = ET.ElementTree(gpx_root)
    tree.write(os.path.join(record_path, "path_%s_%d.gpx"%(task_id, drone_id)))


def record_update(task_id, drone_id, drone_update, record_file):
    # record gps data in gpx format
    with open(record_file, 'a', newline='') as rec:
        c_writer = csv.writer(rec)
        c_writer.writerow([drone_id, drone_update.lat, 
                        drone_update.lon, drone_update.height, 
                        drone_update.battery_power, drone_update.obstacle,
                        drone_update.sig_str])

    # print the parameters
    print("Drone:{} -> latitude={}, longitude={}, height={}, battery-power={}, obstacle={}, signal_strength={}.".format(drone_id, drone_update.lat, 
                                    drone_update.lon, drone_update.height, 
                                    drone_update.battery_power, drone_update.obstacle,
                                    drone_update.sig_str))

def get_base_server_conf(server_config, server_id):
    with open(server_config) as sc:
        servers = json.load(sc)
        for server in servers['base_servers']:
            if server['id'] == server_id:
                return server
    return None

def get_server_for_loc(init_pos):
    with open(server_config) as sc:
        servers = json.load(sc)
        for server in servers['base_servers']:
            if abs(server['location']['lat'] - init_pos[0]) < 10e-6 and abs(server['location']['lon'] - init_pos[1]) < 10e-6:
                return server
    return None

def send_notification(dest_loc, curr_loc, drone_id):

    try:        
        server = get_server_for_loc(dest_loc)
        bl_addr = (server['ip'], server['sync_port'])
        # Create a socket
        sync_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sync_sock.connect(bl_addr)

        print("Successfully connected to server %s:%d"%(bl_addr[0], bl_addr[1]))

        # send init message
        drone_init = BaseSync(drone_id, curr_loc[0], curr_loc[1])
        sync_sock.send(drone_init)

        return True

    except Exception as e:
        print("Failed to notification!!")
        return False

def handle_client(conn, address, task_queue, conflict_mgr, server):
    print("Connected to ", address)

    ack_ok = Ack(True)
    ack_fail = Ack(False)

    # start communication protocol
    try:
        # receive first drone connection message
        buff = conn.recv(sizeof(DroneConnect))
        drone_init = DroneConnect.from_buffer_copy(buff)
        
        # send acknowledgement
        conn.send(ack_ok)

        print("<- Registered drone: %d ->", drone_init.drone_id)

        # Stay in loop till a task is accepted
        while True:
            if is_exit(drone_init.drone_id):
                return

            # if no task then wait
            if not task_queue.task_exists():
                time.sleep(task_wait_sleep_time)
                continue
            
            # send task to initiate the task
            task = task_queue.get_task()

            conn.send(task)

            # wait for acknowledgement
            buff = conn.recv(sizeof(Ack))
            ack_rec = Ack.from_buffer_copy(buff)

            # if task assignment fails, release the task for other drones
            if not ack_rec.is_accepted:
                print("Drone:%d -> Task [%d] rejected."%(drone_init.drone_id, task.task_id))
                task_queue.add_task(task)
                continue
            else:
                print("Drone:%d -> Task [%d] accepted."%(drone_init.drone_id, task.task_id))
                break
            
        # recieve live updates from client
        record_file = os.path.join(record_path,
                "simulation_%s_%d_%s.csv"%(task.task_id, 
                drone_init.drone_id, 
                datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
        
        # register for conflict alert
        dest_loc = (task.dest_lat, task.dest_lon)
        conflict_mgr.add_drone(drone_init.drone_id, dest_loc)
        
        #send sync notification to destination
        send_notification(dest_loc, (server['location']['lat'], server['location']['lon']), drone_init.drone_id)
        
        while True:
            buff = conn.recv(sizeof(DroneUpdate))
            drone_update = DroneUpdate.from_buffer_copy(buff)
            # task complete close connection
            record_update(task.task_id, drone_init.drone_id, drone_update, record_file)
            
            # send alers if any
            is_alert, drone_id = conflict_mgr.get_alert(drone_init.drone_id)
            base_update = BaseUpdate(is_alert, drone_id)
            conn.send(base_update)
            
            if drone_update.is_complete:
                writeGPXDom(record_file, task.task_id, drone_init.drone_id)
                print("Drone:%d -> Task completed successfully."%(drone_init.drone_id))
                conflict_mgr.remove_drone(drone_init.drone_id)
                return

    except BlockingIOError:
        print("socket is open and reading from it would block")
    except ConnectionResetError:
        print("socket was closed")
    # except Exception as e:
    #     print("Unexpected Exception!!")
    
    return

#start drone server
def start_drone_server(server, task_queue, conflict_mgr):
    addr = (server['ip'], server['drone_port'])

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(addr)

    print("Starting base_loc server on [{}] at port {}".format(server['ip'], server['drone_port']))
    try:
        serverSocket.listen()
        while True:
            conn, address = serverSocket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, address, task_queue, conflict_mgr, server))
            thread.start()
    except Exception as e:
        serverSocket.close()

#thread to listen to updates from base locs
def start_sync_server(server, port, conflict_mgr):
    
    addr = (server, port)

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(addr)

    print("Starting sync server on [{}] at port {}".format(server, port))
    try:
        serverSocket.listen()
        while True:
            conn, address = serverSocket.accept()
            buff = conn.recv(sizeof(BaseSync))
            sync_msg = BaseSync.from_buffer_copy(buff)
            conflict_mgr.add_alert((sync_msg.src_lat, sync_msg.src_lon), sync_msg.drone_id)
            conn.close()
    except Exception as e:
        serverSocket.close()

def start_task_sim(task_queue, server_id):
    if server_id == 1:
        task_queue.add_task(BaseTask(1,5,default_dest1[0], default_dest1[1]))
    elif server_id == 2:
        task_queue.add_task(BaseTask(2,5,default_dest2[0], default_dest2[1]))
    while True:
        time.sleep(10)

def main():
    global record_path
    global server_config

    #define the argumes required to be passed for starting the server on base location
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--server-id', help='Assign a unique id for this drone', type=int)
    parser.add_argument('--server-config', help='Server Configuration file', type=str)
    parser.add_argument('--record-dir', help='Driectory to store the simulation records', type=str)
    args = parser.parse_args()

    if args.server_id is None:
        print("--server-id <server id> is necessary")
        exit(1)

    if args.server_config is None:
        print("--server-config <server config file> is necessary")
        exit(1)
    else:
        server_config = args.server_config

    if args.record_dir is not None:
        record_path = args.record_dir

    server = get_base_server_conf(server_config, args.server_id)

    task_queue = TaskQueue()
    conflict_mgr = ConflictMgr()

    #start a task queue thread
    thread_task_sim = threading.Thread(target=start_task_sim, args=(task_queue, args.server_id))
    thread_task_sim.start()

    # start drone server
    thread_drone = threading.Thread(target=start_drone_server, args=(server, task_queue, conflict_mgr))
    thread_drone.start()

    # start sync server in the main thread
    start_sync_server(server['ip'], server['sync_port'], conflict_mgr)

    return

if __name__ == "__main__":
    main()
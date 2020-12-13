import argparse
import socket
import time
import threading
import csv
import os
from payloads import *
import xml.etree.cElementTree as ET

###### Constant Configurations ######
task_wait_sleep_time = 10 # in sec
package_weight = 5 # in kg
default_port = 33001
###### Constant Configurations ######

def task_exists():
    return True

def get_task():
    # read destination coordinates
    return BaseTask(package_weight, 0, 0)

def release_task(task):
    return

# check if exit flag set to any drone
def is_exit(drone_id):
    return False

def writeGPXDom(rec_file):
    
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


def record_update(task_id, drone_id, drone_update):
    # record gps data in gpx format
    record_file = os.path.join("records","simulation_%s_%d.csv"%(task_id, drone_id))
    with open(record_file, 'a', newline='') as rec:
        c_writer = csv.writer(rec)
        c_writer.writerow([drone_id, drone_update.lat, 
                        drone_update.long, drone_update.height, 
                        drone_update.battery_power, drone_update.obstacle,
                        drone_update.sig_str])

    # print the parameters
    print("Drone:{} -> latitude={}, \
        longitude={}, height={}, \
        battery-power={}, obstacle={}, \
        signal_strength={}.".format(drone_id, drone_update.lat, 
                                    drone_update.long, drone_update.height, 
                                    drone_update.battery_power, drone_update.obstacle,
                                    drone_update.sig_str))
    return record_file

def handle_client(conn, address, lock):
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

        while True:
            if is_exit(drone_init.drone_id):
                break
            # if no task then wait
            if not task_exists():
                time.sleep(task_wait_sleep_time)
                continue
            
            # send task to initiate the task
            lock.acquire()
            task = get_task()
            lock.release()

            conn.send(task)

            # wait for acknowledgement
            buff = conn.recv(sizeof(Ack))
            ack_rec = Ack.from_buffer_copy(buff)

            # if task assignment fails, release the task for other drones
            if not ack_rec.is_accepted:
                print("Drone:%d -> Task [%d] rejected"%(drone_init.drone_id, task.task_id))
                lock.acquire()
                release_task(task)
                lock.release()
                break
            
            # recieve live updates from client
            while True:
                buff = conn.recv(sizeof(DroneUpdate))
                drone_update = DroneUpdate.from_buffer_copy(buff)
                # task complete close connection
                rec_file = record_update(task.task_id, drone_init.drone_id, drone_update)
                if drone_update.is_complete:
                    writeGPXDom(rec_file)
                    print("Drone:%d -> Task completed successfully."%(drone_init.drone_id))
                return

    except BlockingIOError:
        print("socket is open and reading from it would block")
    except ConnectionResetError:
        print("socket was closed")
    except Exception as e:
        print("Unexpected Exception!!")
    
    return

def start_server(serverSocket):
    serverSocket.listen()
    while True:
        conn, address = serverSocket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, address))
        thread.start()
    
def main():
    
    #define the argumes required to be passed for starting the server on base location
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--port', help='Port on which server will be started', type=int)

    args = parser.parse_args()

    if args.port is None:
        args.port = default_port

    serv_host = socket.gethostname()
    server = socket.gethostbyname(serv_host)
    addr = (server, args.port)

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(addr)

    print("Starting base_loc server on [{}] at port {}".format(server, args.port))
    start_server(serverSocket)

    return

if __name__ == "__main__":
    main()
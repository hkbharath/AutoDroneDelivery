from ctypes import *

class DroneUpdate(Structure):
    _fields_ = [("lat", c_float),
                ("lon", c_float),
                ("height", c_float),
                ("battery_power", c_uint32),
                ("obstacle",c_bool),
                ("sig_str",c_uint32),
                ("is_moving",c_bool),
                ("is_complete",c_bool)]

class BaseUpdate(Structure):
    _fields_ = [("is_alert", c_bool),
                ("al_drone_id", c_uint32)]

class BaseSync(Structure):
    _fields_ = [("drone_id", c_uint32),
                ("src_lat", c_float),
                ("src_lon", c_float)]

class DroneConnect(Structure):
    _fields_ = [("drone_id", c_uint32),
                ("capacity", c_uint32),
                ("battery_power", c_uint32),
                ("is_recovery", c_bool),
                ("auth_token", c_char_p)]

class BaseTask(Structure):
    _fields_ = [("task_id", c_uint32),
                ("weight", c_uint32),
                ("dest_lat", c_float),
                ("dest_lon", c_float)]

class Ack(Structure):
    _fields_ = [("is_accepted", c_bool)]

class PeerPayload(Structure):
    _fields_ = [("lat", c_float),
                ("lon", c_float),
                ("height", c_float),
                ("Drone_id", c_uint32),
                ("bearing", c_int),
                ("Deviation", c_float)]
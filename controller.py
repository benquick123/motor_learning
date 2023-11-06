import struct 
import socket


class MotorController:
    
    def __init__(self,address="178.172.42.144", port=9005):
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send_position(self, marker_x, marker_y, marker_z):
        data = struct.pack("ddd", marker_x, marker_y, marker_z)
        self.socket.sendto(data, (self.address, self.port))
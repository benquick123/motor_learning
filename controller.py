import struct 
import socket

import numpy as np


class MotorController:
    
    def __init__(self, address="178.172.42.144", port=9005, max_velocity=0.5):
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.force_amplification = 0
        self.max_velocity = max_velocity
        
    def send_position(self, force_x, force_y, force_z):
        data = struct.pack("ddd", force_x, force_y, force_z)
        self.socket.sendto(data, (self.address, self.port))
        
    def get_force(self, velocity):
        assert len(velocity) == 3
        velocity = np.copy(velocity).clip(-self.max_velocity, self.max_velocity)
        return np.abs(velocity) * self.force_amplification
    
    def set_force_amplification(self, force_amplification):
        self.force_amplification = force_amplification
        
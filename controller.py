import struct 
import socket

import numpy as np


class MotorController:
    
    def __init__(self, address="178.172.42.144", port=9005, max_velocity=0.5, direction="forward"):
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.force_amplification = 0
        self.participant_weight = 0
        self.max_velocity = max_velocity

        assert direction in {"forward", "backward"}
        self.direction = 1 if direction == "forward" else -1
        
    def send_force(self, force):
        data = struct.pack("d", force)
        self.socket.sendto(data, (self.address, self.port))
        
    def get_force(self, velocity):
        assert len(velocity) == 3
        velocity = np.copy(velocity).clip(-self.max_velocity, self.max_velocity)
        return self.direction * np.abs(velocity[0]) * self.force_amplification * self.participant_weight
    
    def set_force_amplification(self, force_amplification):
        self.force_amplification = force_amplification

    def set_participant_weight(self, participant_weight):
        self.participant_weight = participant_weight
        
import struct 
import socket

import numpy as np


class MotorController:
    
    def __init__(self, address="178.172.42.144", port=9005, max_velocity=0.5):
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.force_amplification = 0
        self.participant_weight = 0
        self.max_velocity = max_velocity

        self.direction = None
        self.force_mode = None
        
    def send_force(self, force):
        data = struct.pack("d", force)
        self.socket.sendto(data, (self.address, self.port))
        
    def get_force(self, coordinates, perturbation_mode):
        assert len(coordinates) == 3
        assert self.direction is not None, "You have to set direction before obtaining force."
        assert self.force_mode is not None, "You have to set force_mode before obtaining force."
        assert perturbation_mode in {"regular", "channel"}

        if self.force_mode == "regular":
            if perturbation_mode == "regular":
                # we treat the `coordinates` as velocity
                velocity = coordinates
                velocity = np.copy(velocity).clip(-self.max_velocity, self.max_velocity)
                force = self.direction * np.abs(velocity[0]) * self.force_amplification * self.participant_weight
            elif perturbation_mode == "channel":
                # we treat the `coordinates` as position
                position = coordinates
                force = -1 * position[1] * self.force_amplification * self.participant_weight
        else:
            force = 0.0

        if np.isnan(force):
            return 0.0
        return force
    
    def set_force_amplification(self, force_amplification):
        self.force_amplification = force_amplification

    def set_participant_weight(self, participant_weight):
        self.participant_weight = participant_weight

    def set_direction(self, direction):
        assert direction in {"forward", "backward"}
        self.direction = -1 if direction == "forward" else 1

    def set_force_mode(self, force_mode):
        assert force_mode in {"regular", "none"}
        self.force_mode = force_mode
        
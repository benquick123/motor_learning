from time import time
from datetime import datetime
import socket
from multiprocessing import Process, Value
from collections import defaultdict

import numpy as np
from vicon_dssdk import ViconDataStream


MARKER_NAMES = [
    "Left_foot2",
    "Left_foot3",
    "Left_foot_heel",
    "Right_foot2",
    "Right_foot3",
    "Right_foot_heel",
    "Upper_body_left_thigh",
    "Upper_body_neck",
    "Upper_body_right_thigh"
]


class ViconClient:
    
    def __init__(self, subject_name="WholeBodyLearningExp", address="localhost", port=801, velocity_buffer_size=5):
        self.address = address
        self.port = port
        self.client = ViconDataStream.Client()

        self.subject_name = subject_name
        self.prev_marker_positions = dict()
        self.prev_times = dict()

        self.velocity_buffer_size = velocity_buffer_size
        self.velocity_buffer = defaultdict(list)
        
        self.init_connection(self.client)

        self._is_recording = Value("i", 0)
        self.udp_listener = Process(target=self._get_recording_state, args=(self._is_recording, ), daemon=True).start()
        
    def init_connection(self, client):
        client.Connect(self.address + ":" + str(self.port))
        
        # Check the version
        print(f"{datetime.now()} - Connected to Vicon client (v{client.GetVersion()}).")

        # Check setting the buffer size works
        # Set the number of frames that the client should buffer.
        client.SetBufferSize(110)

        #Enable all the data types
        client.EnableSegmentData()
        client.EnableMarkerData()
        client.EnableUnlabeledMarkerData()
        client.EnableMarkerRayData()
        client.EnableDeviceData()
        client.EnableCentroidData()

        # Try setting the different stream modes
        client.SetStreamMode(ViconDataStream.Client.StreamMode.EServerPush)
        # print("Get Frame Push", client.GetFrame(), client.GetFrameNumber())

    def is_recording(self):
        return bool(self._is_recording.value)
    
    def get_current_position(self, name, mode="segment"):
        assert mode in {"segment", "marker", "all_markers"} or isinstance(mode, list), "Mode must be {segment, marker, all_markers}, or a list of marker names."
        
        has_frame = False
        while not has_frame:
            try:
                self.client.GetFrame()
                has_frame = True
            except ViconDataStream.DataStreamException as e:
                print(f"Error: '{str(e)}' ")

        if mode == "segment":
            segment_position = self.client.GetSegmentGlobalTranslation(self.subject_name, name)
            # ^we are only interested in the three coordinates returned here.
            # we want the middle of the segment
            positions = np.array(segment_position[0]) / 1000

        elif mode == "marker":
            marker_position = self.client.GetMarkerGlobalTranslation(self.subject_name, name)
            positions = np.array(marker_position[0]) / 1000
        
        elif mode == "all_markers":
            marker_names = self.client.GetMarkerNames(self.subject_name)
            # marker_positions = self.client.GetLabeledMarkers()

            positions = dict()
            for marker_name in marker_names:
                marker_name = marker_name[0]
                marker_position = self.client.GetMarkerGlobalTranslation(self.subject_name, marker_name)
                positions[marker_name] = np.array(marker_position[0]) / 1000
        
        elif isinstance(mode, list):
            for marker_name in mode:
                marker_position = self.client.GetMarkerGlobalTranslation(self.subject_name, marker_name)
                positions[marker_name] = np.array(marker_position[0]) / 1000
        
        return positions, time()
        
    def get_velocity(self, current_marker_position, current_time, name):
        if name not in self.prev_marker_positions:
            velocity = np.ones(3) * 0
        else:
            velocity = (current_marker_position - self.prev_marker_positions[name]) / (current_time - self.prev_times[name])

        self.prev_marker_positions[name] = np.copy(current_marker_position)
        self.prev_times[name] = current_time

        self.velocity_buffer[name].append(velocity)
        if len(self.velocity_buffer[name]) > self.velocity_buffer_size:
            self.velocity_buffer[name] = self.velocity_buffer[name][1:]

        return np.stack(self.velocity_buffer[name], axis=0).mean(axis=0)

    def get_center_of_pressure(self):
        has_frame = False
        while not has_frame:
            try:
                self.client.GetFrame()
                has_frame = True
            except ViconDataStream.DataStreamException as e:
                print(f"Error: '{str(e)}' ")

        cop0 = np.array(self.client.GetGlobalCenterOfPressure(1)).mean(axis=0)
        cop1 = np.array(self.client.GetGlobalCenterOfPressure(2)).mean(axis=0)

        force_vector_z0 = np.array(self.client.GetGlobalForceVector(1)).mean(axis=0)[2]
        force_vector_z1 = np.array(self.client.GetGlobalForceVector(2)).mean(axis=0)[2]
        force_ratio = force_vector_z0 / (force_vector_z0 + force_vector_z1)
        
        # is averaging the two COP positions correct?
        return cop0 * force_ratio + cop1 * (1 - force_ratio)

    @staticmethod
    def _get_recording_state(is_recording):
        udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_client.bind(("", 30))

        while True:
            data, _ = udp_client.recvfrom(1024)
            data = data.decode('utf-8')
            if "CaptureStart" in data:
                is_recording.value = 1
            elif "CaptureStop" in data:
                is_recording.value = 0

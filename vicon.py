from time import time
from datetime import datetime

import numpy as np
from vicon_dssdk import ViconDataStream


class ViconClient:
    
    def __init__(self, subject_name="WholeBodyLearningExp", address="localhost", port=801):
        self.address = address
        self.port = port
        self.client = ViconDataStream.Client()

        self.subject_name = subject_name
        self.prev_marker_positions = dict()
        self.prev_times = dict()
        
        self.init_connection(self.client)
        
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

    def get_current_position(self, name, mode="segment"):
        assert mode in {"segment", "marker", "all_markers"}
        
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

            return positions, time()

        elif mode == "marker":
            marker_position = self.client.GetMarkerGlobalTranslation(self.subject_name, name)
            positions = np.array(marker_position[0]) / 1000

            return positions, time()
        
        elif mode == "all_markers":
            marker_names = self.client.GetMarkerNames(self.subject_name)
            # marker_positions = self.client.GetLabeledMarkers()

            positions = dict()
            for marker_name in marker_names:
                marker_name = marker_name[0]
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
        
        return velocity
    
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

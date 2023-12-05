from time import time
from datetime import datetime

import numpy as np
from vicon_dssdk import ViconDataStream


class ViconClient:
    
    def __init__(self, subject_name="teast_3_m", address="localhost", port=801):
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
        assert mode in {"segment", "marker"}
        
        has_frame = False
        while not has_frame:
            try:
                self.client.GetFrame()
                has_frame = True
            except ViconDataStream.DataStreamException as e:
                print(f"Error: '{str(e)}' ")

        if mode == "segment":
            data = self.client.GetSegmentGlobalTranslation(self.subject_name, name)
            # ^we are only interested in the three coordinates returned here.
            # we want the middle of the segment
                                
            # Access each vector in function
            # Nexus by default returns position value in mm !!!
            marker_x_axis_m = data[0][0] / 1000
            marker_y_axis_m = -data[0][1] / 1000
            marker_z_axis_m = data[0][2] / 1000
            
            positions = np.array([marker_x_axis_m, marker_y_axis_m, marker_z_axis_m])

            return positions, time()

        elif mode == "marker":
            data = self.client.GetMarkerGlobalTranslation(self.subject_name, name)
            
            # ˇThis needs to be tested and probably debugged.
            marker_x_axis_m = data[0][0] / 1000
            marker_y_axis_m = -data[0][1] / 1000
            marker_z_axis_m = data[0][2] / 1000

            positions = np.array([marker_x_axis_m, marker_y_axis_m, marker_z_axis_m])

            return positions, time()
            
           
    def get_velocity(self, current_marker_position, current_time, name):
        if name not in self.prev_marker_positions:
            velocity = np.ones(3) * 0
        else:
            velocity = (current_marker_position - self.prev_marker_position[name]) / (current_time - self.prev_time[name])

        self.prev_marker_positions[name] = np.copy(current_marker_position)
        self.prev_times[name] = current_time
        
        return velocity
    
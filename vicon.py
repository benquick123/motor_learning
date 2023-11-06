import argparse
from vicon_dssdk import ViconDataStream


class ViconClient:
    
    def __init__(self, subject_name="teast_3_m", segment_name="teast_3_m", address="localhost", port=801):
        self.address = address
        self.port = port
        self.client = ViconDataStream.Client()

        self.subject_name = subject_name
        self.segment_name = segment_name
        
    def init_connection(self, client):
        client.Connect(self.address + ":" + str(self.port))
        
        # Check the version
        print(f"Connected to Vicon client (v{client.GetVersion()}).")

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

    def get_current_position_data(self):
        has_frame = False
        while not has_frame:
            try:
                self.client.GetFrame()
                has_frame = True
            except ViconDataStream.DataStreamException as e:
                print(f"Error: '{str(e)}' ")

        segment_data = self.client.GetSegmentGlobalTranslation(self.subject_name, self.segment_name)
                                
        # Access each vector in function
        # Nexus by default returns position value in mm !!!
        marker_x_axis_m = segment_data[0][0] / 1000
        marker_y_axis_m = -segment_data[0][1] / 1000
        marker_z_axis_m = segment_data[0][2] / 1000

        return marker_x_axis_m, marker_y_axis_m, marker_z_axis_m
           


    
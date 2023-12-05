from vicon import ViconClient

if __name__ == "__main__":
    vicon_client = ViconClient(subject_name="S1", segment_name="Head")
    vicon_client.get_current_position()
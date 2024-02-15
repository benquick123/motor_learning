import json
from time import time, sleep
from datetime import datetime
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import scipy

from vicon import ViconClient
from experiment_logging import Logger
from com_computation import compute_com, create_marker_dict, NOMINAL_HEIGHT, NOMINAL_WEIGHT


class DummyClient:
    
    def __init__(self):
        np.random.seed(42)
    
    def get_current_position(self, name, mode=None):
        return np.random.normal(0, 0.001, size=(3, ))
    
    
def record(total_time, vicon_client, frequency=100):
    recording_start = time()
    
    positions = defaultdict(list)
    while (time() - recording_start) < total_time:
        time_start = time()
        for marker_name, position in vicon_client.get_current_position(None, mode="all_markers")[0].items():
            positions[marker_name].append(position)

        positions["cop"].append(vicon_client.get_center_of_pressure())

        curr_frequency = 1 / (time() - time_start + 1e-8)
        curr_frequency = np.round(curr_frequency, 2)
        curr_frequency = np.clip(curr_frequency, 0, 999)
        print("Capture frequency:", curr_frequency, " " * 20, end="\r")
        if time() - time_start > (1 / frequency):
            pass
            # print(datetime.now(), "- Loop took too much time!", "%.3fs > (1/%d)s" % (time() - time_start, frequency))
        else:
            sleep((1 / frequency) - (time() - time_start))
        
    for marker_name in positions.keys():
        positions[marker_name] = np.stack(positions[marker_name], axis=0)
    return positions


def plot_markers(positions):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    for key, value in positions.items():
        _value = value.copy()
        if key == "com":
            _value[:, 1] = 0
        ax.scatter(_value[:, 0], _value[:, 1], _value[:, 2], label=key)
    plt.legend()
    plt.show()
    

if __name__ == "__main__":
    experiment_config = json.load(open("experiment_config.json", "r"))
    logger = Logger(experiment_config["results_path"], experiment_config["participant"]["id"], no_log=False)
    logger.save_experiment_config(experiment_config, filename="calibration_config.json")
    
    vicon_client = ViconClient()

    ### align feet with hips
    max_distance = 0.01
    thigh_distance = feet_distance = feet_center_displacement = np.inf
    while np.abs(thigh_distance - feet_distance) > max_distance or np.abs(feet_center_displacement) > max_distance:
        time_start = time()
        positions = vicon_client.get_current_position(None, mode="all_markers")[0]
        left_thigh = positions["Upper_body_left_thigh"]
        right_thigh = positions["Upper_body_right_thigh"]
        thigh_distance = np.linalg.norm(left_thigh - right_thigh)
        
        # assuming #3 is the outmost marker on the feet:
        left_outmost_foot = positions["Left_foot3"]
        right_outmost_foot = positions["Right_foot3"]
        feet_distance = np.linalg.norm(left_outmost_foot - right_outmost_foot)

        feet_center_displacement = (left_outmost_foot[0] + right_outmost_foot[0]) / 2

        if feet_center_displacement > max_distance:
            print("Move both feet to the left by", np.abs(np.round(feet_center_displacement, 2)), "m", " " * 20, end="\r")
        elif feet_center_displacement < -max_distance:
            print("Move both feet to the right by", np.abs(np.round(feet_center_displacement, 2)), "m", " " * 20, end="\r")
        elif (thigh_distance - feet_distance) > max_distance:
            # put your feet further apart
            print("Put feet further away by", np.round(thigh_distance - feet_distance, 4), "m", " " * 20, end="\r")
        elif (thigh_distance - feet_distance) < -max_distance:
            # put your feet closer
            print("Put feet closer by", np.round(thigh_distance - feet_distance, 4), "m", " " * 20, end="\r")
        
    print()
    print("Thigh distance:", thigh_distance)
    print("Feet distance:", feet_distance)
    print("Feet center displacement:", feet_center_displacement)
    print("POSITIONING COMPLETE.", "\n")

    ### get measurements related to COM and COP
    max_distance = 0.05 # m
    while True:
        input("Press <Enter> when ready to start recording.")
        
        positions = record(2.0, vicon_client, frequency=experiment_config["refresh_frequency"])
        
        for key, value in positions.items():
            if scipy.spatial.distance.cdist(value, value).max() > max_distance:
                print(f"Too much movement on marker {key}. Try again.")
                break
        else:
            break
        
    height_adjustment_ratio = experiment_config["participant"]["height"] / NOMINAL_HEIGHT
    weight_adjustment_ratio = experiment_config["participant"]["weight"] / NOMINAL_WEIGHT

    for measurement_idx in range(len(positions["Upper_body_left_thigh"])):
        markers = create_marker_dict(positions, measurement_idx, ignore={"com_approx"})
        positions["com_approx"].append(compute_com(markers, height_adjustment_ratio, weight_adjustment_ratio, plot=False))
        
    positions["com_approx"] = np.stack(positions["com_approx"], axis=0)
    
    # do a sanity check over all the positions.
    # note that COM is not supposed to be aligned along the Y axis.
    plot_markers(positions)

    for key, value in positions.items():
        positions[key] = value.mean(axis=0).tolist()

    positions["com_offset"] = np.array(positions["cop"]) - np.array(positions["com_approx"])
    positions["com_offset"][2] = 0
    positions["com_offset"] = positions["com_offset"].tolist()

    print()
    print("COM offsets (x, y, z):")
    print(positions["com_offset"])

    logger.save_com(positions)
    
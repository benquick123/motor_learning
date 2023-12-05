import json
from time import time, sleep
from datetime import datetime
from collections import defaultdict

import numpy as np
import scipy

# from vicon import ViconClient
from experiment_logging import Logger


class DummyClient:
    
    def __init__(self):
        pass
    
    def get_current_position(self, name, mode=None):
        return np.random.normal(0, 0.001, size=(3, ))
    
    
def record(total_time, vicon_client, frequency=100):
    recording_start = time()
    
    positions = defaultdict(list)
    marker_names = ["bos", "left_thigh", "right_thigh", "upper_back"]
    modes = ["segment", "marker", "marker", "marker"]
    while (time() - recording_start) < total_time:
        time_start = time()
        for marker_name, mode in zip(marker_names, modes):
            positions[marker_name].append(vicon_client.get_current_position(marker_name, mode=mode))
        
        if time() - time_start > (1 / frequency):
            print(datetime.now(), "- Loop took too much time!", "%.3fs > (1/%d)s" % (time() - time_start, frequency))
        else:
            sleep((1 / frequency) - (time() - time_start))
        
    for marker_name in marker_names:
        positions[marker_name] = np.stack(positions[marker_name], axis=0)
    return positions


if __name__ == "__main__":
    experiment_config = json.load(open("experiment_config.json", "r"))
    logger = Logger(experiment_config["results_path"], experiment_config["participant"]["id"], no_log=False)
    
    vicon_client = DummyClient()
    
    np.random.seed(42)
    # max distance is the same as in FSL measurements.
    max_distance = 0.02 # m
    
    while True:
        input("Press <Enter> when ready to start recording.")
        
        positions = record(2.0, vicon_client, frequency=experiment_config["refresh_frequency"])
        
        for value in positions.values():    
            if scipy.spatial.distance.cdist(value, value).max() > max_distance:
                print("Too much movement. Try again.")
                break
        else:
            break
        
    nominal_height = 1.78 # m
    nominal_weight = 77.9 # kg
    nominal_lh2 = 0.1488 # m
    nominal_lh3 = 0.0825 # m
    
    adjustment_ratio = experiment_config["participant"]["height"] / nominal_height
    lh2 = adjustment_ratio * nominal_lh2
    lh3 = adjustment_ratio * nominal_lh3
    
    # get the marker positions relative to the centre of bos:
    positions["left_thigh"] -= positions["bos"]
    positions["right_thigh"] -= positions["bos"]
    positions["upper_back"] -= positions["bos"]
    
    # get the lower_back point position
    midpoint = 0.5 * (positions["left_thigh"] + positions["right_thigh"])
    
    # we derive the left-right thigh angle
    # assuming y axis is the one we are not interested in
    thigh_displacement = positions["right_thigh"] - positions["left_thigh"]
    thigh_angle = np.arctan(thigh_displacement[2] / thigh_displacement[0]) # in radians
    positions["lower_back"] = midpoint.copy()
    positions["lower_back"][0] += np.sin(thigh_angle) * lh2
    positions["lower_back"][2] += np.cos(thigh_angle) * lh2
    
    # get the actual center of mass
    # first, get the angle in y plane of the line going through lower and upper back
    back_displacement = positions["upper_back"] - positions["lower_back"]
    back_angle = np.arctan(back_displacement[2] / thigh_displacement[0])
    # from the angle, get the COM
    positions["com"] = positions["lower_back"].copy()
    positions["com"][0] += np.sin(back_angle) * lh3
    positions["com"][1] = None
    positions["com"][2] += np.cos(back_angle) * lh3
    
    for key, value in positions.items():
        positions[key] = value.mean(axis=0).tolist()
        
    logger.save_com(positions)
    
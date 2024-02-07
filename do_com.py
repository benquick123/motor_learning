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

        if time() - time_start > (1 / frequency):
            print(datetime.now(), "- Loop took too much time!", "%.3fs > (1/%d)s" % (time() - time_start, frequency))
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
    
    vicon_client = ViconClient()
    
    # max distance is the same as in FSL measurements.
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

    print("COM offsets (x, y, z):")
    print(positions["com_offset"])

    logger.save_com(positions)
    
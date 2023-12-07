import json
from time import time, sleep
from datetime import datetime
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import scipy

from vicon import ViconClient
from experiment_logging import Logger
from com_computation import compute_com, NOMINAL_HEIGHT


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
    max_distance = 0.020 # m
    
    while True:
        input("Press <Enter> when ready to start recording.")
        
        positions = record(2.0, vicon_client, frequency=experiment_config["refresh_frequency"])
        
        for value in positions.values():
            if scipy.spatial.distance.cdist(value, value).max() > max_distance:
                print("Too much movement. Try again.")
                break
        else:
            break
        
    adjustment_ratio = experiment_config["participant"]["height"] / NOMINAL_HEIGHT

    for measurement_idx in range(len(positions["Upper_body_left_thigh"])):
        positions["com"].append(compute_com(positions["Upper_body_left_thigh"][measurement_idx],
                                            positions["Upper_body_right_thigh"][measurement_idx],
                                            positions["Upper_body_neck"][measurement_idx],
                                            adjustment_ratio))
        
    positions["com"] = np.stack(positions["com"], axis=0)
    
    # do a sanity check over all the positions.
    # note that COM is not supposed to be aligned along the Y axis.
    plot_markers(positions)

    for key, value in positions.items():
        positions[key] = value.mean(axis=0).tolist()

    positions["com"][1] = None
        
    logger.save_com(positions)
    
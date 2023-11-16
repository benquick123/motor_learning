import json
from time import time, sleep
from datetime import datetime

import numpy as np
import scipy
from collections import defaultdict

# from vicon import ViconClient
from experiment_logging import Logger


class DummyClient:
    
    def __init__(self):
        pass
    
    def get_current_position(self):
        return np.random.normal(0, 0.001, size=(3, ))


def record_one_direction(total_time, vicon_client, frequency=100):
    recording_start = time()
    
    positions = []
    while (time() - recording_start) < total_time:
        time_start = time()
        positions.append(vicon_client.get_current_position())
        
        if time() - time_start > (1 / frequency):
            print(datetime.now(), "- Loop took too much time!", "%.3fs > (1/%d)s" % (time() - time_start, frequency))
        else:
            sleep((1 / frequency) - (time() - time_start))
        
    positions = np.stack(positions, axis=0)
    return positions
    

if __name__ == "__main__":
    # vicon_client = ViconClient()
    experiment_config = json.load(open("experiment_config.json", "r"))
    
    vicon_client = DummyClient()
    logger = Logger(experiment_config["results_path"], experiment_config["participant"]["id"], no_log=False)
    
    direction_dict = {0: "LEFT", 1: "RIGHT", 2: "FORWARD", 3: "BACKWARD", 4: "LEFT_45_DEG", 5: "RIGHT_45_DEG"}
    
    np.random.seed(42)
    max_distance = 0.02 # we allow max movement of 2 cm during measurements.
    fsl_order = np.random.permutation(list(direction_dict.keys())).tolist() + np.random.permutation(list(direction_dict.keys())).tolist()
    fsl_results = defaultdict(list)
    print(fsl_order)
    
    fsl_idx = 0
    while fsl_idx < len(fsl_order):
        print(direction_dict[fsl_order[fsl_idx]])
        
        input("Press <Enter> where ready to start recording.")
        
        positions = record_one_direction(2.0, vicon_client, frequency=experiment_config["refresh_frequency"])
        positions_mean = positions.mean(axis=0)
        
        if scipy.spatial.distance.cdist(positions, positions).max() > max_distance:
            print("Too much movement. Try again.")
            continue

        fsl_results[direction_dict[fsl_order[fsl_idx]]].append(positions_mean)
        fsl_idx += 1
        
    all_datapoints = []
    for key in fsl_results:
        fsl_results[key] = np.stack(fsl_results[key], axis=0).mean(axis=0).tolist()
        all_datapoints.append(fsl_results[key])
        
    all_datapoints = np.stack(all_datapoints, axis=0)    
    fsl_results["fsl_geom_mean"] = scipy.stats.gmean(all_datapoints, axis=0).tolist()
    fsl_results["fsl_arith_mean"] = scipy.stats.tmean(all_datapoints, axis=0).tolist()
    
    logger.save_fsl(fsl_results)

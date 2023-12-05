import argparse
import json
import traceback
from datetime import datetime
from time import sleep, time

import numpy as np
import pygame

from experiment_logging import Logger
# from vicon import ViconClient
# from controller import MotorController
from interface import Interface
from state_machine import StateMachine


def initialize_state_dict(experiment_config):
    state_dict = {}
    state_dict["frequency"] = experiment_config["refresh_frequency"]
    state_dict["force_amplification"] = experiment_config["experiment"]["force_amplification"]
    state_dict["total_time"] = experiment_config["experiment"]["total_time"]
    state_dict["state_wait_time_range"] = experiment_config["experiment"]["state_wait_time_range"]
    
    state_dict["current_force_amplification"] = 0
    state_dict["main_circle_offset"] = np.zeros(2)
    
    state_dict["experiment_start"] = -1
    state_dict["show_progress_bar"] = False
    state_dict["show_remaining_time"] = False
    state_dict["show_score"] = False
    state_dict["state_wait_time"] = -1
    
    # Samsung S32A704NWU monitor
    # state_dict["pixels_per_mm"] = 5.42
    # When using mouse as input
    # state_dict["pixels_per_mm"] = 1
    state_dict["pixels_per_mm"] = experiment_config["interface"]["pixels_per_mm"]
    
    return state_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_log", action="store_true", help="Disable logging")
    args = parser.parse_args()
    
    experiment_config = json.load(open("experiment_config.json", "r"))
    state_dict = initialize_state_dict(experiment_config)
    
    # vicon_client = ViconClient()
    # controller = MotorController()
    interface = Interface()
    state_machine = StateMachine()
    logger = Logger(experiment_config["results_path"], experiment_config["participant"]["id"], no_log=args.no_log)
    
    logger.save_experiment_config(experiment_config)
    
    continue_loop = True
    try:
        while continue_loop:
            time_start = time()
            pygame.event.get()
            
            # get marker position
            # marker_position, marker_timestamp = vicon_client.get_current_position()
            
            # calculate velocity
            # marker_velocity = vicon_client.get_velocity(marker_position, timestamp)
            
            # update state dict
            # state_dict["marker_position"] = marker_position
            state_dict["marker_position"] = np.array(list(pygame.mouse.get_pos()) + [0])
            # state_dict["marker_velocity"] = marker_velocity
            # state_dict["marker_timestamp"] = marker_timestamp
            state_dict["marker_timestamp"] = time()
                    
            # send data to motor controller
            # motor_force = controller.get_force(marker_velocity)
            # state_dict["motor_force"] = motor_force
            # controller.set_force_amplification(state_dict["current_force_amplification"])
            # controller.send_position(*motor_force)
            
            state_dict["enter_pressed"] = pygame.key.get_pressed()[pygame.K_RETURN]
            
            continue_loop, state_dict = state_machine.maybe_update_state(state_dict)
            
            # update interface
            interface.update(state_dict)
            interface.draw()
            
            # save current state to file
            logger.save_datapoint(state_dict)
            
            # calculate time and optionally wait
            if time() - time_start > (1 / state_dict["frequency"]):
                print(datetime.now(), "- Loop took too much time!", "%.3fs > (1/%d)s" % (time() - time_start, state_dict["frequency"]))
            else:
                sleep((1 / state_dict["frequency"]) - (time() - time_start))
                
    except Exception:
        print(traceback.format_exc())
    finally:    
        logger.close()
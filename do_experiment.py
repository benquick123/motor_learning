import argparse
import json
import traceback
from datetime import datetime
from time import sleep, time

import numpy as np
import pygame
import os

from experiment_logging import Logger
from vicon import ViconClient
from controller import MotorController
from interface import Interface
from state_machine import StateMachine
from com_computation import compute_com, NOMINAL_HEIGHT, NOMINAL_WEIGHT
from cbos_computation import compute_cbos


def initialize_state_dict(state_dict, experiment_config, block_idx, total_blocks):
    if state_dict is None:
        state_dict = {}
        state_dict["state_wait_time"] = -1

    state_dict["frequency"] = experiment_config["refresh_frequency"]
    state_dict["force_amplification"] = experiment_config["experiment"][block_idx]["force_amplification"]
    state_dict["channel_amplification"] = experiment_config["experiment"][block_idx]["channel_amplification"]
    state_dict["total_time"] = experiment_config["experiment"][block_idx]["total_time"]
    state_dict["total_trials"] = state_dict["remaining_trials"] = experiment_config["experiment"][block_idx]["total_trials"]
    state_dict["remaining_perc"] = 1.0
    state_dict["state_wait_time_range"] = experiment_config["experiment"][block_idx]["state_wait_time_range"]
    state_dict["desired_trial_time"] = experiment_config["experiment"][block_idx]["desired_trial_time"]
    state_dict["catch_trial_idxs"] = experiment_config["experiment"][block_idx]["catch_trial_idxs"]
    state_dict["channel_trial_idxs"] = experiment_config["experiment"][block_idx]["channel_trial_idxs"]
    state_dict["perturbation_mode"] = "regular"
    state_dict["pause_duration"] = experiment_config["experiment_pause_duration"]
    
    state_dict["current_force_amplification"] = 0
    state_dict["main_circle_offset"] = np.zeros(2)
    
    state_dict["experiment_start"] = -1
    state_dict["show_progress_bar"] = False
    state_dict["show_remaining_time"] = False
    state_dict["show_score"] = False
    state_dict["current_state"] = StateMachine.INITIAL_SCREEN

    state_dict["total_blocks"] = total_blocks
    state_dict["block_idx"] = block_idx
    
    state_dict["pixels_per_m"] = experiment_config["interface"]["pixels_per_m"]

    state_dict["height_adjustment_ratio"] = experiment_config["participant"]["height"] / NOMINAL_HEIGHT
    state_dict["weight_adjustment_ratio"] = experiment_config["participant"]["weight"] / NOMINAL_WEIGHT

    state_dict["needs_update"] = False
    
    return state_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_log", action="store_true", help="Disable logging")
    parser.add_argument("--debug", action="store_true", help="Enable debugging, i.e. mouse controlled COM.")
    args = parser.parse_args()
    
    experiment_config = json.load(open("experiment_config.json", "r"))
    
    vicon_client = ViconClient()
    interface = Interface(display_number=1, main_circle_buffer_size=2)
    state_machine = StateMachine()

    logger = Logger(experiment_config["results_path"], experiment_config["participant"]["id"], no_log=args.no_log)
    logger.save_experiment_config(experiment_config)
    
    controller = MotorController()
    controller.set_participant_weight(experiment_config["participant"]["weight"])

    assert os.path.exists(os.path.join(logger.results_path, logger.participant_folder, "participant_com.json")), "Run do_before.py first to obtain participant's COM."
    participant_com = json.load(open(os.path.join(logger.results_path, logger.participant_folder, "participant_com.json"), "r"))
    
    continue_loop = True
    state_dict = None
    block_idx, total_blocks = 0, len(experiment_config["experiment"])
    try:
        while continue_loop:
            if state_dict is None or state_dict["needs_update"]:
                state_dict = initialize_state_dict(state_dict, experiment_config, block_idx, total_blocks)
                controller.set_direction(experiment_config["experiment"][block_idx]["force_direction"])
                controller.set_force_mode(experiment_config["experiment"][block_idx]["force_mode"])
                block_idx += 1

            time_start = time()
            pygame.event.get()
            
            # get marker position
            positions = {}
            for marker_name, marker_position in vicon_client.get_current_position(None, mode="all_markers")[0].items():
                state_dict[marker_name] = marker_position

            state_dict["com_approx"] = compute_com(state_dict, state_dict["height_adjustment_ratio"], state_dict["weight_adjustment_ratio"])
            state_dict["com"] = state_dict["com_approx"] + participant_com["com_offset"]
            
            # calculate velocity
            state_dict["marker_timestamp"] = time()
            marker_velocity = vicon_client.get_velocity(state_dict["com"], state_dict["marker_timestamp"], "com")
            
            # update state dict
            if args.debug:
                state_dict["marker_position"] = np.array(list(pygame.mouse.get_pos()) + [0]) / 1000
            else:
                state_dict["marker_position"] = state_dict["com"]

            state_dict["marker_velocity"] = marker_velocity
            if "cbos" not in state_dict:
                state_dict["cbos"] = compute_cbos(state_dict)
                    
            # send data to motor controller
            controller.set_force_amplification(state_dict["current_force_amplification"])
            if state_dict["perturbation_mode"] == "regular":
                motor_force = controller.get_force(marker_velocity, state_dict["perturbation_mode"])
            elif state_dict["perturbation_mode"] == "channel":
                motor_force = controller.get_force(state_dict["marker_position"] - state_dict["cbos"], state_dict["perturbation_mode"])
            else:
                print("Incorrect perturbation mode: " + str(state_dict["perturbation_mode"]))
                raise NotImplementedError
            state_dict["motor_force"] = motor_force
            # print(motor_force, end="\r")
            controller.send_force(motor_force)
            
            state_dict["enter_pressed"] = pygame.key.get_pressed()[pygame.K_RETURN]
            
            continue_loop, state_dict = state_machine.maybe_update_state(state_dict)
            
            # update interface
            interface.update(state_dict)
            interface.draw()
            
            # save current state to file
            logger.save_datapoint(state_dict)
            
            # calculate time and optionally wait
            curr_frequency = 1 / (time() - time_start + 1e-8)
            curr_frequency = np.round(curr_frequency, 2)
            curr_frequency = np.clip(curr_frequency, 0, 999)
            # print("Capture frequency:", curr_frequency, " " * 20, end="\r")
            if time() - time_start > (1 / state_dict["frequency"]):
                pass
                # print(datetime.now(), "- Loop took too much time!", "%.3fs > (1/%d)s" % (time() - time_start, state_dict["frequency"]), end="\r")
            else:
                sleep(np.abs((1 / state_dict["frequency"]) - (time() - time_start)))
                
        print()
    except Exception:
        print(traceback.format_exc())
    finally:    
        logger.close()
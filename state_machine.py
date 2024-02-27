from time import time

import numpy as np
from interface import Colors


class StateMachine:
    
    INITIAL_SCREEN = 0
    
    GO_TO_MIDDLE_CIRCLE = 1
    IN_MIDDLE_CIRCLE = 2
    GO_OUT_OF_MIDDLE_CIRCLE = 3
    
    GO_TO_LEFT_CIRCLE_AFTER_TRIAL = 4
    GO_TO_RIGHT_CIRCLE_AFTER_TRIAL = 5

    GO_TO_LEFT_CIRCLE = 6
    IN_LEFT_CIRCLE = 7
    STAY_IN_LEFT_CIRCLE = 8
    GO_OUT_OF_LEFT_CIRCLE = 9

    GO_TO_RIGHT_CIRCLE = 10
    IN_RIGHT_CIRCLE = 11
    STAY_IN_RIGHT_CIRCLE = 12
    GO_OUT_OF_RIGHT_CIRCLE = 13

    TRIAL_TERMINATION = 14
    PAUSE = 15
    EXIT = 16
    
    def __init__(self):
        self.current_state = None
        self.prev_main_circle_position = None
        self.maybe_next_state = None
        
        # construct reverse state lookup
        all_variables = vars(StateMachine)
        self.reverse_state_lookup = {all_variables[name]: name for name in all_variables if isinstance(all_variables[name], int) and name.isupper()}
    
    def maybe_update_state(self, state_dict):
        continue_loop = True
        
        #### WHEN NONE
        if self.current_state is None:
            self.current_state = StateMachine.INITIAL_SCREEN
            self.set_initial_screen(state_dict)

        #### AT THE BEGINNING
        elif self.current_state == StateMachine.INITIAL_SCREEN:
            if state_dict["enter_pressed"]:
                self.current_state = StateMachine.GO_TO_MIDDLE_CIRCLE
                self.set_start_experiment(state_dict)
                self.set_go_to_middle_circle(state_dict)

        elif self.current_state == StateMachine.GO_TO_MIDDLE_CIRCLE:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["middle_circle_position"]) < state_dict["middle_circle_radius"]:
                self.current_state = StateMachine.IN_MIDDLE_CIRCLE
                self.set_in_middle_circle(state_dict)

        elif self.current_state == StateMachine.IN_MIDDLE_CIRCLE:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.GO_TO_LEFT_CIRCLE_AFTER_TRIAL
                self.set_go_to_left_circle_after_trial(state_dict)
            elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["middle_circle_position"]) > state_dict["middle_circle_radius"]:
                self.current_state = StateMachine.GO_TO_MIDDLE_CIRCLE
                self.set_go_to_middle_circle(state_dict)

        #### GO TO THE LEFT / RIGHT AFTER INITIATION ENDS, OR AFTER TRIAL
        elif self.current_state == StateMachine.GO_TO_LEFT_CIRCLE_AFTER_TRIAL:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["left_circle_position"]) < state_dict["left_circle_radius"]:
                self.current_state = StateMachine.IN_LEFT_CIRCLE
                self.set_in_left_circle(state_dict)

        elif self.current_state == StateMachine.GO_TO_RIGHT_CIRCLE_AFTER_TRIAL:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["right_circle_position"]) < state_dict["right_circle_radius"]:
                self.current_state = StateMachine.IN_RIGHT_CIRCLE
                self.set_in_right_circle(state_dict)

        #### WHEN WAITING IN THE LEFT / RIGHT CIRCLE TO GO OUT
        elif self.current_state == StateMachine.IN_LEFT_CIRCLE:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.GO_OUT_OF_LEFT_CIRCLE
                self.set_go_out_of_left_circle(state_dict)
                self.prev_time = time()
            elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["left_circle_position"]) > state_dict["left_circle_radius"]:
                self.current_state = StateMachine.GO_TO_LEFT_CIRCLE_AFTER_TRIAL
                self.set_go_to_left_circle_after_trial(state_dict)

        elif self.current_state == StateMachine.IN_RIGHT_CIRCLE:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.GO_OUT_OF_RIGHT_CIRCLE
                self.set_go_out_of_right_circle(state_dict)
                self.prev_time = time()
            elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["right_circle_position"]) > state_dict["right_circle_radius"]:
                self.current_state = StateMachine.GO_TO_RIGHT_CIRCLE_AFTER_TRIAL
                self.set_go_to_right_circle_after_trial(state_dict)

        #### WHEN TRIAL STARTS
        elif self.current_state == StateMachine.GO_OUT_OF_LEFT_CIRCLE:
            self.prev_time = time()

            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["left_circle_position"]) >= state_dict["left_circle_radius"]:
                self.current_state = StateMachine.GO_TO_RIGHT_CIRCLE
                self.set_go_to_right_circle(state_dict)
                self.prev_time = time()

        elif self.current_state == StateMachine.GO_OUT_OF_RIGHT_CIRCLE:
            self.prev_time = time()

            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["right_circle_position"]) >= state_dict["right_circle_radius"]:
                self.current_state = StateMachine.GO_TO_LEFT_CIRCLE
                self.set_go_to_left_circle(state_dict)
                self.prev_time = time()

        #### WHEN TRIAL IS IN PROGRESS
        elif self.current_state in {StateMachine.GO_TO_RIGHT_CIRCLE, StateMachine.GO_TO_LEFT_CIRCLE}:
            self.prev_time = time()
            circle_reached = False

            if self.current_state == StateMachine.GO_TO_RIGHT_CIRCLE:
                maybe_next_state = StateMachine.STAY_IN_RIGHT_CIRCLE
                side = "right"
            else:
                maybe_next_state = StateMachine.STAY_IN_LEFT_CIRCLE
                side = "left"
            
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict[side + "_circle_position"]) < state_dict[side + "_circle_radius"]:
                circle_reached = True

            elif (side == "right" and state_dict["main_circle_position"][0] > state_dict[side + "_circle_position"][0]) or \
                 (side == "left" and state_dict["main_circle_position"][0] < state_dict[side + "_circle_position"][0]):
                
                if self._get_line_distance_to_center(self.prev_main_circle_position, state_dict["main_circle_position"], state_dict[side + "_circle_position"]) < state_dict[side + "_circle_radius"]:
                    self.set_unsuccessful_trial(state_dict, side)
                else:
                    self.set_unsuccessful_trial(state_dict, side)
                
                circle_reached = True

            if circle_reached:
                # time() is measured above, and saved to prev_time.
                # hardcoded check if the trial took more than 2.0 seconds; in this case, the trial will be repeated.
                # NOTE: the results will still be saved in the logs. Take care to exclude the trial during analysis.
                if self.prev_time - state_dict["state_start_time"] < 2.0:
                    state_dict["remaining_trials"] += -1
                if self.prev_time - state_dict["state_start_time"] < state_dict["desired_trial_time"][0]:
                    self.set_too_fast(state_dict)
                elif self.prev_time - state_dict["state_start_time"] > state_dict["desired_trial_time"][1]:
                    self.set_too_slow(state_dict)
                self.current_state = maybe_next_state
                self.set_trial_termination(state_dict)

        #### WHEN TRIAL ENDED, BUT WE DON'T WANT THE PARTICIPANT TO OVERSHOOT
        elif self.current_state in {StateMachine.STAY_IN_LEFT_CIRCLE, StateMachine.STAY_IN_RIGHT_CIRCLE}:
            self.prev_time = time()
            trial_terminated = False

            if self.current_state == StateMachine.STAY_IN_RIGHT_CIRCLE:
                maybe_next_state = StateMachine.GO_TO_RIGHT_CIRCLE_AFTER_TRIAL
                side = "right"
            else:
                maybe_next_state = StateMachine.GO_TO_LEFT_CIRCLE_AFTER_TRIAL
                side = "left"

            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = maybe_next_state
                self.set_successful_trial(state_dict, side)
                trial_terminated = True

            elif np.linalg.norm(state_dict["main_circle_position"] - state_dict[side + "_circle_position"]) > state_dict[side + "_circle_radius"]:
                self.set_unsuccessful_trial(state_dict, side)
                trial_terminated = True

            if trial_terminated:
                self.current_state = maybe_next_state
                self.set_trial_termination(state_dict)
                
        elif self.current_state == StateMachine.PAUSE:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.GO_TO_MIDDLE_CIRCLE
                self.set_unpause(state_dict)
                self.set_initial_screen(state_dict)
                self.set_start_experiment(state_dict)
                self.set_go_to_middle_circle(state_dict)

        elif self.current_state == StateMachine.EXIT:
            if state_dict["enter_pressed"]:
                continue_loop = False
        
        if state_dict["remaining_trials"] == 0 and \
           self.current_state not in {StateMachine.PAUSE, StateMachine.STAY_IN_RIGHT_CIRCLE, StateMachine.STAY_IN_LEFT_CIRCLE, StateMachine.GO_TO_RIGHT_CIRCLE_AFTER_TRIAL, StateMachine.GO_TO_LEFT_CIRCLE_AFTER_TRIAL}:
            if state_dict["block_idx"] < state_dict["total_blocks"] - 1:
                self.current_state = StateMachine.PAUSE
                self.set_pause(state_dict)
                state_dict["needs_update"] = True
            else:
                self.current_state = StateMachine.EXIT
                self.set_exit(state_dict)

        if state_dict is not None and "main_circle_position" in state_dict:
            self.prev_main_circle_position = np.copy(state_dict["main_circle_position"])
            
        return continue_loop, state_dict

    def _get_line_distance_to_center(self, p0, p1, c):
        # https://www.wikiwand.com/en/Distance_from_a_point_to_a_line#:~:text=horizontal%20line%20segment.-,Line%20defined%20by%20two%20points,-If%20the%20line

        numerator = np.abs((p1[0] - p0[0]) * (p0[1] - c[1]) - (p0[0] - c[0]) * (p1[1] - p0[1]))
        denominator = np.linalg.norm(p0 - p1)
        return numerator / denominator

    def set_initial_screen(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Press <Enter> when ready."
        state_dict["remaining_trials"] = state_dict["total_trials"]
        state_dict["score"] = 0
        
        state_dict["main_circle_color"] = Colors.BLACK
        state_dict["middle_circle_color"] = Colors.BLACK
        state_dict["left_circle_color"] = Colors.BLACK
        state_dict["right_circle_color"] = Colors.BLACK

    def set_start_experiment(self, state_dict):
        state_dict["experiment_start"] = time()
        state_dict["score"] = 0
        state_dict["main_circle_offset"] = (state_dict["marker_position"] - state_dict["cbos"]) # * state_dict["pixels_per_m"]
        state_dict["show_progress_bar"] = True
        state_dict["show_remaining_time"] = state_dict["show_score"] = False
        state_dict["main_text"] = ""
        state_dict["main_circle_color"] = Colors.LIGHT_GRAY

    def set_go_to_middle_circle(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["middle_circle_color"] = Colors.DARK_GRAY

    def set_in_middle_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 2.0 # s
        state_dict["middle_circle_color"] = Colors.BLUE

    def set_go_to_left_circle_after_trial(self, state_dict):
        state_dict["state_start_time"] = None
        # state_dict["main_text"] = ""
        state_dict["middle_circle_color"] = Colors.BLACK
        if state_dict["left_circle_color"] == Colors.BLACK:
            state_dict["left_circle_color"] = Colors.BLUE
        state_dict["right_circle_color"] = Colors.DARK_GRAY
    
    def set_go_to_right_circle_after_trial(self, state_dict):
        state_dict["state_start_time"] = None
        # state_dict["main_text"] = ""
        state_dict["middle_circle_color"] = Colors.BLACK
        state_dict["left_circle_color"] = Colors.DARK_GRAY
    
    def set_in_left_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"])

    def set_in_right_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = np.random.uniform(*state_dict["state_wait_time_range"])
        
    def set_go_out_of_left_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["main_text"] = ""
        state_dict["left_circle_color"] = Colors.DARK_GRAY
        state_dict["right_circle_color"] = Colors.BLUE
    
    def set_go_out_of_right_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["main_text"] = ""
        state_dict["left_circle_color"] = Colors.BLUE
        state_dict["right_circle_color"] = Colors.DARK_GRAY

    def set_go_to_left_circle(self, state_dict):
        self.set_go_to_circle(state_dict)
    
    def set_go_to_right_circle(self, state_dict):
        self.set_go_to_circle(state_dict)
        
    def set_go_to_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["current_force_amplification"] = state_dict["force_amplification"]
        state_dict["perturbation_mode"] = "regular"

        # handle the catch trials.
        current_trial_idx = state_dict["total_trials"] - state_dict["remaining_trials"]
        if "catch_trial_idxs" in state_dict and isinstance(state_dict["catch_trial_idxs"], list) and len(state_dict["catch_trial_idxs"]) > 0:
            if current_trial_idx in state_dict["catch_trial_idxs"]:
                state_dict["current_force_amplification"] = 0
        # handle the channel trials.
        elif "channel_trial_idxs" in state_dict and isinstance(state_dict["channel_trial_idxs"], list) and len(state_dict["channel_trial_idxs"]) > 0:
            if current_trial_idx in state_dict["channel_trial_idxs"]:
                state_dict["perturbation_mode"] = "channel"
                state_dict["current_force_amplification"] = state_dict["channel_amplification"]

    def set_successful_trial(self, state_dict, side):
        state_dict["score"] += 1
        state_dict[side + "_circle_color"] = Colors.DARK_GREEN
        
    def set_unsuccessful_trial(self, state_dict, side):
        state_dict[side + "_circle_color"] = Colors.RED
        
    def set_too_fast(self, state_dict):
        state_dict["main_text"] = "Too fast!"

    def set_too_slow(self, state_dict):
        state_dict["main_text"] = "Too slow!"

    def set_trial_termination(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = 0.5
        state_dict["current_force_amplification"] = 0

        state_dict["remaining_trials"] = int(np.clip(state_dict["remaining_trials"], a_min=0, a_max=state_dict["total_trials"]))
        state_dict["remaining_perc"] = state_dict["remaining_trials"] / state_dict["total_trials"]
        state_dict["current_state"] = self.reverse_state_lookup[self.current_state]

    def set_pause(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["state_wait_time"] = state_dict["pause_duration"]
        state_dict["current_force_amplification"] = 0
        state_dict["main_text"] = "Experiment paused for %d seconds." % state_dict["pause_duration"]

    def set_unpause(self, state_dict):
        state_dict["main_text"] = ""

    def set_exit(self, state_dict):
        state_dict["main_circle_color"] = Colors.BLACK
        state_dict["left_circle_color"] = Colors.BLACK
        state_dict["right_circle_color"] = Colors.BLACK
        
        state_dict["current_force_amplification"] = 0
        state_dict["show_progress_bar"] = state_dict["show_remaining_time"] = state_dict["show_score"] = False
        
        state_dict["main_text"] = "Press <Enter> to exit."
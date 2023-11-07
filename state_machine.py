from time import time

import numpy as np
from interface import Colors


class StateMachine:
    
    INITIAL_SCREEN = 0
    GO_TO_START_CIRCLE = 1
    IN_START_CIRCLE = 2
    GO_TO_TERMINAL_CIRCLE = 3
    GO_TO_TERMINAL_CIRCLE_REPEAT = 4
    IN_TERMINAL_CIRCLE = 5
    EXIT = 6
    
    def __init__(self):
        self.current_state = None
    
    def maybe_update_state(self, state_dict):
        continue_loop = True
        
        if self.current_state is None:
            self.current_state = StateMachine.INITIAL_SCREEN
            self.set_initial_screen(state_dict)
        
        elif self.current_state == StateMachine.INITIAL_SCREEN:
            if state_dict["enter_pressed"]:
                self.current_state = StateMachine.GO_TO_START_CIRCLE
                self.set_start_experiment(state_dict)
                self.set_go_to_start_circle(state_dict)
                
        elif self.current_state == StateMachine.GO_TO_START_CIRCLE:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["start_circle_position"]) < state_dict["start_circle_radius"]:
                self.current_state = StateMachine.IN_START_CIRCLE
                self.set_in_start_circle(state_dict)
        
        elif self.current_state == StateMachine.IN_START_CIRCLE:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.GO_TO_TERMINAL_CIRCLE
                self.set_go_to_terminal_circle(state_dict)
            elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["start_circle_position"]) > state_dict["start_circle_radius"]:
                self.current_state = StateMachine.GO_TO_START_CIRCLE
                self.set_go_to_start_circle(state_dict)
        
        elif self.current_state == StateMachine.GO_TO_TERMINAL_CIRCLE:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["terminal_circle_position"]) < state_dict["terminal_circle_radius"]:
                self.current_state = StateMachine.IN_TERMINAL_CIRCLE
                self.set_successful_trial(state_dict)
                self.set_in_terminal_circle(state_dict)
                
        elif self.current_state == StateMachine.GO_TO_TERMINAL_CIRCLE_REPEAT:
            if np.linalg.norm(state_dict["main_circle_position"] - state_dict["terminal_circle_position"]) < state_dict["terminal_circle_radius"]:
                self.current_state = StateMachine.IN_TERMINAL_CIRCLE
                self.set_in_terminal_circle(state_dict)
                
        elif self.current_state == StateMachine.IN_TERMINAL_CIRCLE:
            if time() - state_dict["state_start_time"] >= state_dict["state_wait_time"]:
                self.current_state = StateMachine.GO_TO_START_CIRCLE
                self.set_go_to_start_circle(state_dict)
            elif np.linalg.norm(state_dict["main_circle_position"] - state_dict["terminal_circle_position"]) > state_dict["terminal_circle_radius"]:
                self.current_state = StateMachine.GO_TO_TERMINAL_CIRCLE_REPEAT
                self.set_go_to_terminal_circle(state_dict)
                
        elif self.current_state == StateMachine.EXIT:
            if state_dict["enter_pressed"]:
                continue_loop = False
            
        if "experiment_start" in state_dict:
            if time() - state_dict["experiment_start"] >= state_dict["total_time"]:
                self.current_state = StateMachine.EXIT
                self.set_exit(state_dict)
                
            state_dict["remaining_time"] = np.clip(state_dict["total_time"] - (time() - state_dict["experiment_start"]), a_min=0, a_max=state_dict["total_time"])
            state_dict["remaining_time_perc"] = state_dict["remaining_time"] / state_dict["total_time"]
        else:
            state_dict["remaining_time"] = state_dict["total_time"]
            state_dict["remaining_time_perc"] = 1.0
            
        return continue_loop, state_dict

    def set_initial_screen(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["main_text"] = "Press <Enter> when ready."
        state_dict["remaining_time"] = state_dict["total_time"]
        state_dict["score"] = 0
        
        state_dict["main_circle_color"] = Colors.WHITE
        state_dict["start_circle_color"] = Colors.WHITE
        state_dict["terminal_circle_color"] = Colors.WHITE
        
    def set_start_experiment(self, state_dict):
        state_dict["experiment_start"] = time()
        state_dict["main_circle_offset"] = state_dict["main_circle_position"] - state_dict["screen_center_position"]
        state_dict["show_progress_bar"] = state_dict["show_remaining_time"] = state_dict["show_score"] = True
        state_dict["main_text"] = ""
        state_dict["main_circle_color"] = Colors.GREEN

    def set_go_to_start_circle(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["start_circle_color"] = Colors.RED
        state_dict["terminal_circle_color"] = Colors.PURPLE
    
    def set_in_start_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["start_circle_color"] = Colors.DARK_GREEN

    def set_go_to_terminal_circle(self, state_dict):
        state_dict["state_start_time"] = None
        state_dict["start_circle_color"] = Colors.PURPLE
        state_dict["terminal_circle_color"] = Colors.RED
        state_dict["current_force_amplification"] = state_dict["force_amplification"]
        
    def set_successful_trial(self, state_dict):
        state_dict["score"] += 1
        state_dict["current_force_amplification"] = 0
        
    def set_in_terminal_circle(self, state_dict):
        state_dict["state_start_time"] = time()
        state_dict["terminal_circle_color"] = Colors.DARK_GREEN
        
    def set_out_terminal_circle(self, state_dict):
        state_dict["terminal_circle_color"] = Colors.RED

    def set_exit(self, state_dict):
        state_dict["main_circle_color"] = Colors.WHITE
        state_dict["start_circle_color"] = Colors.WHITE
        state_dict["terminal_circle_color"] = Colors.WHITE
        
        state_dict["show_progress_bar"] = state_dict["show_remaining_time"] = state_dict["show_score"] = False
        
        state_dict["main_text"] = "Press <Enter> to exit."
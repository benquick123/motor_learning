import numpy as np
import pygame


class Colors:
    
    WHITE = (255, 255, 255)
    PURPLE = (77, 77, 255)
    GREEN = (0, 204, 0)
    DARK_GREEN = (0, 150, 0)
    BLACK = (16, 16, 16)
    RED = (204, 0, 51)
    BLUE = (46, 81, 219)
    LIGHT_GRAY = (224, 224, 224)
    DARK_GRAY = (128, 128, 128)

class Interface:
    
    def __init__(self, display_number=1, main_circle_buffer_size=5):
        self.display_number = display_number
        
        pygame.init()
        pygame.display.set_caption("Experiment")

        self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, display=display_number)
        self.window_width, self.window_height = pygame.display.get_window_size()
        
        self.main_font = pygame.font.SysFont(None, 56)
        self.font = pygame.font.SysFont(None, 48)
        
        self.main_circle_buffer_size = main_circle_buffer_size
        self.main_circle_buffer = []
    
    def update(self, state_dict):
        if "main_circle_position" not in state_dict:
            state_dict["main_circle_radius"] = 0.002 * state_dict["pixels_per_m"]
            state_dict["main_circle_color"] = Colors.BLACK
        if "middle_circle_position" not in state_dict:
            state_dict["middle_circle_position"] = np.array([self.window_width / 2, self.window_height / 2])
            # TODO: change this to r = 0.005m
            state_dict["middle_circle_radius"] = 0.005 * state_dict["pixels_per_m"]
            state_dict["middle_circle_color"] = Colors.BLACK
        if "right_circle_position" not in state_dict:
            # TODO: change this to actual measurement on the screen, e.g. 0.05m from the center.
            state_dict["right_circle_position"] = np.array(state_dict["middle_circle_position"])
            state_dict["right_circle_position"][0] += 0.05 * state_dict["pixels_per_m"]
            # TODO: change this to r = 0.005m
            state_dict["right_circle_radius"] = 0.005 * state_dict["pixels_per_m"]
            state_dict["right_circle_color"] = Colors.BLACK
        if "left_circle_position" not in state_dict:
            state_dict["left_circle_position"] = np.array(state_dict["middle_circle_position"])
            state_dict["left_circle_position"][0] -= 0.05 * state_dict["pixels_per_m"]
            state_dict["left_circle_radius"] = 0.005 * state_dict["pixels_per_m"]
            state_dict["left_circle_color"] = Colors.BLACK
        if "screen_center_position" not in state_dict:
            state_dict["screen_center_position"] = np.array([self.window_width / 2, self.window_height / 2])
        
        # update the raw marker position to reflect the position on screen
        position_x = self.window_width / 2 + (state_dict["marker_position"][0] - state_dict["cbos"][0]) * state_dict["pixels_per_m"] - state_dict["main_circle_offset"][0]
        position_y = self.window_height / 2 + (state_dict["marker_position"][1] - state_dict["cbos"][1]) * state_dict["pixels_per_m"] - state_dict["main_circle_offset"][1]
        self.main_circle_buffer.append(np.array([position_x, position_y]))
        if len(self.main_circle_buffer) > self.main_circle_buffer_size:
            self.main_circle_buffer = self.main_circle_buffer[1:]
            
        state_dict["main_circle_position"] = np.stack(self.main_circle_buffer, axis=0).mean(axis=0)
        
        self.state_dict = state_dict
    
    def draw(self):
        self.window.fill(Colors.BLACK)
        
        self._draw_left_circle()
        self._draw_middle_circle()
        self._draw_right_circle()
        self._draw_main_circle()
        
        self._draw_progress_bar()
        self._draw_remaining_time()
        self._draw_score()
        
        self._draw_main_text()
        
        pygame.display.update()
        
    def _draw_middle_circle(self):
        pygame.draw.circle(self.window, 
                           self.state_dict["middle_circle_color"], 
                           self.state_dict["middle_circle_position"], 
                           self.state_dict["middle_circle_radius"])
    
    def _draw_left_circle(self):
        pygame.draw.circle(self.window, 
                           self.state_dict["left_circle_color"], 
                           self.state_dict["left_circle_position"], 
                           self.state_dict["left_circle_radius"])
        
    def _draw_right_circle(self):
        pygame.draw.circle(self.window, 
                           self.state_dict["right_circle_color"],
                           self.state_dict["right_circle_position"],
                           self.state_dict["right_circle_radius"])
        
    def _draw_main_circle(self):
        pygame.draw.circle(self.window,
                           self.state_dict["main_circle_color"],
                           self.state_dict["main_circle_position"],
                           self.state_dict["main_circle_radius"])
    
    def _draw_progress_bar(self):
        if self.state_dict.get("show_progress_bar", None):
            pygame.draw.rect(self.window, Colors.RED, pygame.Rect(0, 0.02 * self.window_height, self.window_width, 0.05 * self.window_height))
            pygame.draw.rect(self.window, Colors.DARK_GREEN, pygame.Rect(0, 0.02 * self.window_height, self.window_width * self.state_dict["remaining_time_perc"], 0.05 * self.window_height))
    
    def _draw_remaining_time(self):
        if self.state_dict.get("show_remaining_time", None):
            remaining_time = np.round(self.state_dict["remaining_time"], 1)
            render = self.font.render(f"Remaining time: {remaining_time}", True, Colors.WHITE)
            render_position_x = 0.005 * self.window_width
            render_position_y = 0.09 * self.window_height
            self.window.blit(render, (render_position_x, render_position_y))
    
    def _draw_score(self):
        if self.state_dict.get("show_remaining_time", None):
            score = str(np.round(self.state_dict["score"], 1)).zfill(4)
            render = self.font.render(f"Score: {score}", True, Colors.WHITE)
            render_position_x = 0.995 * self.window_width - render.get_width()
            render_position_y = 0.09 * self.window_height
            self.window.blit(render, (render_position_x, render_position_y))
    
    def _draw_main_text(self):
        if self.state_dict.get("main_text", ""):
            render = self.main_font.render(self.state_dict["main_text"], True, Colors.WHITE)
            render_position_x = self.window_width / 2 - render.get_width() / 2
            render_position_y = self.window_height / 2 - render.get_height() / 2
            self.window.blit(render, (render_position_x, render_position_y))
    

if __name__ == "__main__":
    interface = Interface()
    from time import sleep
    
    sleep(1)
    interface.update()
    interface.draw()
    sleep(4)
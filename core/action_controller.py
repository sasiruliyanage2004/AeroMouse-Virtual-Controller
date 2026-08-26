from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
import ctypes
import time

class ActionController:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.scroll_speed = 3
        
        user32 = ctypes.windll.user32
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        
        self.prev_x = self.screen_width // 2
        self.prev_y = self.screen_height // 2
        
        self.last_click_time = 0
        self.last_action_time = 0

    def move_to(self, x_ratio, y_ratio):
        margin = 0.15 
        x_ratio = (x_ratio - margin) / (1 - 2 * margin)
        y_ratio = (y_ratio - margin) / (1 - 2 * margin)
        
        x_ratio = max(0.0, min(1.0, x_ratio))
        y_ratio = max(0.0, min(1.0, y_ratio))
        
        target_x = int(x_ratio * self.screen_width)
        target_y = int(y_ratio * self.screen_height)
        
        smooth_factor = 0.3
        curr_x = int(self.prev_x + (target_x - self.prev_x) * smooth_factor)
        curr_y = int(self.prev_y + (target_y - self.prev_y) * smooth_factor)
        
        self.mouse.position = (curr_x, curr_y)
        self.prev_x = curr_x
        self.prev_y = curr_y

    def click(self):
        current_time = time.time()
        if current_time - self.last_click_time > 0.3:
            self.mouse.click(Button.left)
            self.last_click_time = current_time
            print("Left Clicked!")

    def scroll(self, direction):
        self.mouse.scroll(0, direction * self.scroll_speed)

    def minimize_window(self):
        current_time = time.time()
        if current_time - self.last_action_time > 2.0:
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.press(Key.down)
                self.keyboard.release(Key.down)
            self.last_action_time = current_time
            print("Minimized Window!")
            
    def maximize_window(self):
        current_time = time.time()
        if current_time - self.last_action_time > 2.0:
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.press(Key.up)
                self.keyboard.release(Key.up)
            self.last_action_time = current_time
            print("Maximized Window!")

    def close_window(self):
        current_time = time.time()
        if current_time - self.last_action_time > 2.0:
            with self.keyboard.pressed(Key.alt):
                self.keyboard.press(Key.f4)
                self.keyboard.release(Key.f4)
            self.last_action_time = current_time
            print("Closed Window!")

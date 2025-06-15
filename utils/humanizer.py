import subprocess
import random
import time

def human_typing(text, min_delay=0.08, max_delay=0.2):
    for c in text:
        subprocess.typewrite(c)
        time.sleep(random.uniform(min_delay, max_delay))

def move_cursor_naturally(x, y):
    current_x, current_y = subprocess.position()
    steps = random.randint(10, 20)
    for i in range(steps):
        intermediate_x = current_x + (x - current_x) * i / steps
        intermediate_y = current_y + (y - current_y) * i / steps
        subprocess.moveTo(intermediate_x, intermediate_y, duration=0.01)

def wait_random(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

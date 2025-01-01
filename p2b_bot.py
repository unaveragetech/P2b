import pyautogui
import psutil
import time
import os
import json
import threading
from PIL import ImageGrab
import ollama
import logging
import tkinter as tk
import re
import ast
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# File paths
SHARED_DIR = "shared"
LOG_FILE = os.path.join(SHARED_DIR, "minecraft_logs.txt")
SCREENSHOT_FILE = os.path.join(SHARED_DIR, "screenshot.png")
MINESCRIPT_FOLDER = os.path.join(SHARED_DIR, "minescripts/")
BARITONE_COMMANDS_FILE = os.path.join(SHARED_DIR, "baritone_commands.json")
POTENTIAL_SCRIPTS_FOLDER = os.path.join(SHARED_DIR, "potential_scripts/")
VIEWPORT_SETTINGS_FILE = os.path.join(SHARED_DIR, "viewport_settings.json")
EXAMPLE_COMMANDS_FILE = os.path.join(SHARED_DIR, "example_commands.json")

# Ensure directories exist
os.makedirs(SHARED_DIR, exist_ok=True)
os.makedirs(MINESCRIPT_FOLDER, exist_ok=True)
os.makedirs(POTENTIAL_SCRIPTS_FOLDER, exist_ok=True)

# Load Baritone commands and example commands
with open(BARITONE_COMMANDS_FILE, 'r') as f:
    baritone_commands = json.load(f)
with open(EXAMPLE_COMMANDS_FILE, 'r') as f:
    example_commands = json.load(f)

# Load viewport settings
try:
    with open(VIEWPORT_SETTINGS_FILE, 'r') as f:
        viewport_settings = json.load(f)
except FileNotFoundError:
    viewport_settings = {
        "x": 100,
        "y": 100,
        "width": 800,
        "height": 600
    }

# Viewport class
class Viewport:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def expand(self, direction, pixels):
        if direction == 'left':
            self.x -= pixels
            self.width += pixels
        elif direction == 'right':
            self.width += pixels
        elif direction == 'up':
            self.y -= pixels
            self.height += pixels
        elif direction == 'down':
            self.height += pixels

    def contract(self, direction, pixels):
        if direction == 'left':
            self.x += pixels
            self.width -= pixels
        elif direction == 'right':
            self.width -= pixels
        elif direction == 'up':
            self.y += pixels
            self.height -= pixels
        elif direction == 'down':
            self.height -= pixels

    def get_coordinates(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)

# Overlay window class
class OverlayWindow:
    def __init__(self, viewport):
        self.viewport = viewport
        self.root = tk.Toplevel()
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.5)
        self.root.geometry(f"{viewport.width}x{viewport.height}+{viewport.x}+{viewport.y}")
        self.root.bind('<Button-1>', self.on_click)
        self.root.bind('<B1-Motion>', self.on_drag)
        self.root.bind('<ButtonRelease-1>', self.on_release)
        self.root.bind('<Configure>', self.on_configure)
        self.root.lift()
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg='red')

    def on_click(self, event):
        self.x = event.x
        self.y = event.y

    def on_drag(self, event):
        new_x = self.root.winfo_x() + event.x - self.x
        new_y = self.root.winfo_y() + event.y - self.y
        self.root.geometry(f"+{new_x}+{new_y}")

    def on_release(self, event):
        pass

    def on_configure(self, event):
        self.viewport.x = self.root.winfo_x()
        self.viewport.y = self.root.winfo_y()
        self.viewport.width = self.root.winfo_width()
        self.viewport.height = self.root.winfo_height()
        with open(VIEWPORT_SETTINGS_FILE, 'w') as f:
            json.dump({
                "x": self.viewport.x,
                "y": self.viewport.y,
                "width": self.viewport.width,
                "height": self.viewport.height
            }, f)

# Initialize viewport and overlay
viewport = Viewport(**viewport_settings)
overlay = OverlayWindow(viewport)

# Ollama context
OLLAMA_CONTEXT = """
You are a Minecraft bot assistant using:
1. Baritone: Send commands in-game via chat, e.g., `#goto x y z`, `#mine block_name`.
2. PyAutoGUI: Control game interactions with key presses, e.g., `press w`, `open chat`.
3. MineScript: Execute Python scripts in-game with `/minescript script_name`.

Choose the appropriate framework based on game context, logs, and screen info.
"""

# Function to check if Minecraft is running
def is_minecraft_running():
    for proc in psutil.process_iter(['name']):
        if "Minecraft" in proc.info.get('name', ''):
            return True
    return False

# Function to read Minecraft logs
def read_logs():
    if not os.path.exists(LOG_FILE):
        logging.warning(f"Log file not found: {LOG_FILE}")
        return []
    try:
        with open(LOG_FILE, "r") as file:
            return file.readlines()
    except IOError as e:
        logging.error(f"Failed to read logs: {e}")
        return []

# Function to write commands to in-game chat
def write_to_chat(command):
    try:
        pyautogui.press("t")  # Open chat
        time.sleep(0.3)
        pyautogui.typewrite(command)
        pyautogui.press("enter")  # Send command
        time.sleep(0.3)
    except Exception as e:
        logging.error(f"Failed to write to chat: {e}")

# Function to capture a screenshot of the game window
def capture_screenshot():
    try:
        x1, y1, x2, y2 = viewport.get_coordinates()
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        screenshot.save(SCREENSHOT_FILE)
    except Exception as e:
        logging.error(f"Failed to capture screenshot: {e}")

# Function to analyze the screen with Ollama
def analyze_screen():
    try:
        with open(SCREENSHOT_FILE, "rb") as image_file:
            image_data = image_file.read()
        response = ollama.chat(
            model="llava",
            messages=[{"role": "system", "content": "Explain the context of this game screen."}],
            image=image_data
        )
        return response.message.content
    except Exception as e:
        logging.error(f"Failed to analyze screen: {e}")
        return ""

# Function to generate a response from Ollama
def generate_response(logs, screen_context):
    try:
        messages = [
            {"role": "system", "content": OLLAMA_CONTEXT},
            {"role": "user", "content": f"Game Logs:\n{''.join(logs)}\nScreen Context:\n{screen_context}"}
        ]
        response = ollama.chat(model="llama3.2", messages=messages)
        return response.message.content
    except Exception as e:
        logging.error(f"Failed to generate response: {e}")
        return ""

# Function to execute commands
def execute_command(command):
    try:
        if command.startswith("baritone:"):
            cmd_key = command.replace("baritone:", "").strip()
            if cmd_key in baritone_commands:
                write_to_chat(baritone_commands[cmd_key])
            else:
                logging.warning(f"Unknown Baritone command: {cmd_key}")
        elif command.startswith("pyautogui:"):
            action = command.replace("pyautogui:", "").strip()
            if action == "press w":
                pyautogui.keyDown("w")
                time.sleep(0.3)
                pyautogui.keyUp("w")
            elif action == "open chat":
                pyautogui.press("t")
        elif command.startswith("minescript:"):
            script_name = command.replace("minescript:", "").strip()
            write_to_chat(f"/minescript {script_name}")
        else:
            logging.warning(f"Unknown command format: {command}")
    except Exception as e:
        logging.error(f"Failed to execute command: {e}")

# Script verification
def verify_script(script_path):
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()
        ast.parse(script_content)  # Syntax check
        # Additional compliance checks can be added here
        return True
    except Exception as e:
        logging.error(f"Script verification failed: {e}")
        return False

# Move script to Minescript folder
def move_script_to_minescript(script_path):
    try:
        os.rename(script_path, os.path.join(MINESCRIPT_FOLDER, os.path.basename(script_path)))
        logging.info(f"Moved script to Minescript folder: {os.path.basename(script_path)}")
    except Exception as e:
        logging.error(f"Failed to move script: {e}")

# Function to fetch example commands
def fetch_example_commands(task_type):
    if task_type in example_commands:
        return example_commands[task_type]
    else:
        logging.warning(f"No examples found for task type: {task_type}")
        return []

# Function to fetch and parse Baritone commands
def fetch_baritone_commands():
    response = requests.get("https://baritone.leijurv.com/commands")
    soup = BeautifulSoup(response.text, "html.parser")
    commands = []

    # Example: Find all command elements (adjust based on actual HTML structure)
    for cmd in soup.find_all("code", class_="command"):
        commands.append(cmd.text.strip())

    return commands

# Function to fetch and parse Minescript commands
def fetch_minescript_commands():
    response = requests.get("https://minescript.net/docs")
    soup = BeautifulSoup(response.text, "html.parser")
    commands = []

    # Example: Find all command elements (adjust based on actual HTML structure)
    for cmd in soup.find_all("code", class_="minescript-command"):
        commands.append(cmd.text.strip())

    return commands

# Function to save commands to a JSON file
def save_commands(commands, filename):
    with open(filename, "w") as f:
        json.dump(commands, f, indent=4)
    print(f"Saved {len(commands)} commands to {filename}")

# Main monitoring loop
def monitor_minecraft():
    while True:
        if is_minecraft_running():
            logs = read_logs()
            capture_screenshot()
            screen_context = analyze_screen()
            response = generate_response(logs, screen_context)
            logging.info(f"Generated response: {response}")
            execute_command(response)
            # Check for viewport adjustment commands
            viewport_command_pattern = re.compile(r'(expand|contract) viewport (left|right|up|down) by (\d+) pixels')
            match = viewport_command_pattern.search(response)
            if match:
                action = match.group(1)
                direction = match.group(2)
                pixels = int(match.group(3))
                if action == 'expand':
                    viewport.expand(direction, pixels)
                elif action == 'contract':
                    viewport.contract(direction, pixels)
                overlay.on_configure(None)
            # Check for script generation
            if os.path.exists(POTENTIAL_SCRIPTS_FOLDER):
                for script_file in os.listdir(POTENTIAL_SCRIPTS_FOLDER):
                    script_path = os.path.join(POTENTIAL_SCRIPTS_FOLDER, script_file)
                    if verify_script(script_path):
                        move_script_to_minescript(script_path)
                    else:
                        os.remove(script_path)
                        logging.warning(f"Deleted invalid script: {script_file}")
        else:
            logging.info("Minecraft not running. Waiting...")
        time.sleep(1)  # Adjust sleep time as needed

# Function to manage interaction with Ollama
def main():
    print("Starting Player-to-Bot (P2B) system...")
    logging.info("Starting P2B system...")
    threading.Thread(target=monitor_minecraft, daemon=True).start()
    try:
        while True:
            time.sleep(1)  # Keep the main thread running
    except KeyboardInterrupt:
        logging.info("P2B system stopped by user.")

if __name__ == "__main__":
    main()

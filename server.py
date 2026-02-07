#!/usr/bin/env python3

from fastmcp import FastMCP
from src.emulator import PokemonEmulator
from src.constants import *
import os

# Initialize FastMCP
mcp = FastMCP("Pokemon Blue Strategy Guide")

from src.navigation import Navigation
from src.battle import Battle
from src.game_state import GameState

from PIL.Image import Image
import asyncio
import threading
import time

import queue
import json

# Global Instances
emulator = None
navigation = None
battle = None
game_state = None

# Thread-safe Command Queue
command_queue = queue.Queue()
response_queue = queue.Queue()

def run_on_main(func_name, *args, **kwargs):
    """Sends a command to the main thread and waits for the result."""
    command_queue.put((func_name, args, kwargs))
    # Wait for the response from main thread
    success, result = response_queue.get()
    if not success:
        raise result
    return result

def get_emulator_info():
    """Returns info about the global instances (safe to call from background)."""
    global emulator, navigation, battle, game_state
    return emulator, navigation, battle, game_state

# Updated Tools to use Queue
@mcp.tool()
async def get_local_map() -> str:
    """Returns the current map ID, position, and visual grid."""
    return run_on_main("get_local_map")

@mcp.tool()
async def walk_to(x: int, y: int, on_battle: str = "interrupt", avoid_positions: list = None) -> str:
    """
    Moves the player to the target coordinate (x, y).
    on_battle: "interrupt" (default), "run", or "fight".
    avoid_positions: Optional list of (x, y) coordinates to avoid during pathfinding.
    """
    return run_on_main("walk_to", x, y, on_battle, avoid_positions)

@mcp.tool()
async def get_player_status() -> str:
    """
    Returns the current Map ID, (X, Y) coordinates, and nearby points of interest.
    Use this if walk_to fails or if you need to verify your exact position.
    """
    return run_on_main("get_player_status")

@mcp.tool()
async def move_direction(direction: str, steps: int = 1) -> str:
    """
    Moves the player in a direction for a number of steps.
    If steps is None, moves until blocked, a battle starts, or a map transition occurs.
    """
    return run_on_main("move_direction", direction, steps)

@mcp.tool()
async def execute_battle_turn(action: str) -> str:
    """Executes a high-level battle action."""
    return run_on_main("execute_battle_turn", action)

@mcp.tool()
async def get_party_info() -> str:
    """Returns a JSON summary of the current party."""
    return run_on_main("get_party_info")

@mcp.tool()
async def read_journal() -> str:
    """Returns a summary of the game journal."""
    return run_on_main("read_journal")

@mcp.tool()
async def write_journal_entry(note: str) -> str:
    """Log a persistent note about the game state."""
    return run_on_main("write_journal_entry", note)

@mcp.tool()
async def advance_dialogue() -> str:
    """Mashes the A button until the current dialogue box is closed."""
    return run_on_main("advance_dialogue")

@mcp.tool()
async def describe_tile(x: int, y: int, coordinate_type: str = "screen") -> str:
    """
    Returns a semantic description of a tile (e.g., 'Wall', 'Door').
    coordinate_type: 'screen' (default, 0-19, 0-17) or 'map' (absolute coords).
    """
    return run_on_main("describe_tile", x, y, coordinate_type)

@mcp.tool()
async def press_button(button: str) -> str:
    """Presses a raw button (a, b, start, select, up, down, left, right)."""
    return run_on_main("press_button", button)

@mcp.tool()
async def wait(seconds: float) -> str:
    """Waits for a number of seconds in game time. Useful for loading or animations."""
    return run_on_main("wait", seconds)

@mcp.tool()
async def get_dialogue_text() -> str:
    """Reads the text currently visible in the on-screen dialogue box."""
    return run_on_main("get_dialogue_text")

@mcp.tool()
async def get_full_screen_text() -> str:
    """Read all text currently on the entire screen. Useful for menus and title screens."""
    return run_on_main("get_full_screen_text")

@mcp.tool()
async def get_visual_observation() -> str:
    """
    Captures a screenshot of the game. 
    Workflow: Call this tool, then use your `read_file` or equivalent tool on 'last_observation.png' 
    to see and describe the game screen (menus, characters, etc.) yourself.
    """
    img = run_on_main("screen_image")
    img.save("last_observation.png")
    return "Visual observation saved to 'last_observation.png'. Use your file tools to read and interpret this image now."

@mcp.tool()
async def save_game(name: str = "default") -> str:
    """Saves the current position and state of the game. Use before risky actions."""
    filename = f"saves/{name}.state"
    os.makedirs("saves", exist_ok=True)
    return run_on_main("save_state", filename)

@mcp.tool()
async def load_game(name: str = "default") -> str:
    """Loads a previously saved game state."""
    filename = f"saves/{name}.state"
    return run_on_main("load_state", filename)

@mcp.tool()
async def read_ram_region(start_address: int, length: int) -> str:
    """Read a range of RAM bytes. Useful for debugging specific memory flags."""
    return run_on_main("read_ram_region", start_address, length)

@mcp.tool()
async def press_buttons(sequence: str) -> str:
    """
    Presses a sequence of buttons separated by commas.
    Example: 'start,wait,a'
    Available: a, b, start, select, up, down, left, right, wait
    """
    return run_on_main("press_buttons", sequence)

def init_emulator(rom_path):
    global emulator, navigation, battle, game_state
    if not os.path.exists(rom_path):
         raise FileNotFoundError(f"ROM file not found at {os.path.abspath(rom_path)}")
    
    headless_env = os.getenv("HEADLESS", "true").lower() == "true"
    print(f"Initializing Emulator (Headless={headless_env})...")
    
    emulator = PokemonEmulator(rom_path, headless=headless_env)
    battle = Battle(emulator)
    navigation = Navigation(emulator, battle)
    game_state = GameState(emulator)

def process_command(func_name, args, kwargs):
    """Executes a command using the global instances (Called on Main Thread)."""
    try:
        if func_name == "get_local_map":
            return True, json.dumps(navigation.get_local_map())
        elif func_name == "get_player_status":
            return True, str(navigation.get_player_status())
        elif func_name == "move_direction":
            return True, str(emulator.move_direction(*args, **kwargs))
        elif func_name == "walk_to":
            return True, navigation.walk_to(*args, **kwargs)
        elif func_name == "execute_battle_turn":
            return True, battle.execute_action(*args, **kwargs)
        elif func_name == "get_party_info":
            return True, json.dumps(game_state.get_party_info())
        elif func_name == "read_journal":
            return True, json.dumps(game_state.read_journal())
        elif func_name == "read_ram_region":
            return True, str(emulator.read_ram_region(*args, **kwargs))
        elif func_name == "write_journal_entry":
            return True, game_state.write_journal_entry(*args, **kwargs)
        elif func_name == "advance_dialogue":
            return True, emulator.advance_dialogue()
        elif func_name == "describe_tile":
            return True, navigation.describe_tile(*args, **kwargs)
        elif func_name == "get_dialogue_text":
            return True, emulator.get_dialogue_text()
        elif func_name == "get_full_screen_text":
            return True, emulator.get_full_screen_text()
        elif func_name == "get_visual_observation":
            return True, emulator.screen_image()
        elif func_name == "screen_image":
            return True, emulator.screen_image()
        elif func_name == "save_state":
            return True, emulator.save_state(*args, **kwargs)
        elif func_name == "load_state":
            return True, emulator.load_state(*args, **kwargs)
        elif func_name == "wait":
            return True, emulator.wait(*args, **kwargs)
        elif func_name == "press_button":
            button = args[0]
            valid = ["a", "b", "start", "select", "up", "down", "left", "right"]
            if button.lower() not in valid:
                return True, f"Invalid button: {button}"
            emulator.input(button.lower())
            return True, f"Pressed {button}"
        elif func_name == "press_buttons":
            seq = args[0].split(",")
            valid = ["a", "b", "start", "select", "up", "down", "left", "right"]
            for b in seq:
                b = b.strip().lower()
                if b == "wait":
                    emulator.tick(60)
                elif b in valid:
                    emulator.input(b)
                time.sleep(0.05) # Tiny gap between macro commands
            return True, f"Executed sequence: {args[0]}"
    except Exception as e:
        return False, e
    return False, Exception(f"Unknown command: {func_name}")

if __name__ == "__main__":
    try:
        init_emulator("PokemonBlue.gb")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        exit(1)

    # Start MCP in a background thread
    threading.Thread(target=lambda: mcp.run(), daemon=True).start()

    print("System Ready. Main thread ticking GUI...")

    try:
        while True:
            # 1. Process pending commands from MCP tools
            try:
                # Check for one command per tick to keep GUI responsive
                func_name, args, kwargs = command_queue.get_nowait()
                result = process_command(func_name, args, kwargs)
                response_queue.put(result)
            except queue.Empty:
                pass

            # 2. Tick Emulator
            if not emulator.tick(1):
                break
            
            time.sleep(0.01) # Yield a bit
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Main loop crash: {e}")

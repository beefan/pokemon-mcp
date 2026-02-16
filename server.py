#!/usr/bin/env python3

from fastmcp import FastMCP
from src.emulator import PokemonEmulator
from src.constants import *
import os
import queue
import json
import datetime
import threading
import time

# Initialize FastMCP
mcp = FastMCP("Pokemon Blue Strategy Guide")

from src.navigation import Navigation
from src.battle import Battle
from src.game_state import GameState
from src.vision import VisionSystem
from src.collision import CollisionGrid

# Global Instances
emulator = None
navigation = None
battle = None
game_state = None
vision = None
collision = None

# Thread-safe Command Queue
command_queue = queue.Queue()
response_queue = queue.Queue()

# Auto-checkpoint config
AUTO_CHECKPOINT_ENABLED = True
AUTO_SAVE_PREFIX = "auto_"
AUTO_STATE_EXTENSION = ".state"
AUTO_CHECKPOINT_LIMIT = 50

def run_on_main(func_name, *args, **kwargs):
    command_queue.put((func_name, args, kwargs))
    success, result = response_queue.get()
    if not success:
        raise result
    return result

def _auto_checkpoint(reason: str, note: str = ""):
    if not AUTO_CHECKPOINT_ENABLED: return None
    return run_on_main("auto_checkpoint", reason, note)

def _auto_checkpoint_filename():
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    return f"{AUTO_SAVE_PREFIX}{timestamp}{AUTO_STATE_EXTENSION}"

def _prune_auto_checkpoints():
    os.makedirs("saves", exist_ok=True)
    auto_files = []
    for fname in os.listdir("saves"):
        if not (fname.startswith(AUTO_SAVE_PREFIX) and fname.endswith(AUTO_STATE_EXTENSION)):
            continue
        path = os.path.join("saves", fname)
        auto_files.append((path, os.path.getmtime(path)))
    if len(auto_files) <= AUTO_CHECKPOINT_LIMIT:
        return
    auto_files.sort(key=lambda item: item[1])
    for path, _ in auto_files[:-AUTO_CHECKPOINT_LIMIT]:
        os.remove(path)

def _log_navigation_event(tool_name: str, result: str):
    if game_state is None: return
    game_state.write_journal_entry(f"NavLog [{tool_name}]: {result}")

# --- TOOLS ---

@mcp.tool()
async def get_screen_analysis() -> str:
    """
    CORE VISION TOOL: Captures the game screen and returns an analysis with a visual grid.
    Returns: JSON with map_id, position, and 'image_path' to the annotated screenshot.
    """
    return run_on_main("get_screen_analysis")

@mcp.tool()
async def get_local_map(radius: int = 6) -> str:
    """
    Returns a detailed local map scan including tile IDs, walkability, and allowed directions.
    Use this to understand the environment and plan moves.
    """
    return run_on_main("get_local_map", radius)

@mcp.tool()
async def walk_to(x: int, y: int, on_battle: str = "interrupt") -> str:
    """
    PRIMARY NAVIGATION: Moves the player to a coordinate within the current map.
    Handles obstacle avoidance and pathfinding.
    """
    result = run_on_main("walk_to", x, y, on_battle)
    _log_navigation_event("walk_to", result)
    return result

@mcp.tool()
async def move_direction(direction: str, steps: int = 1) -> str:
    """
    Manual movement: Moves the player in a direction.
    Useful for precise positioning or scouting.
    """
    result = run_on_main("move_direction", direction, steps)
    if AUTO_CHECKPOINT_ENABLED: _auto_checkpoint(f"move_{direction}")
    return result

@mcp.tool()
async def interact_with(x: int, y: int) -> str:
    """
    Interacts with an object at map coordinates (x, y).
    automatically walks to the nearest side of the object and presses 'A'.
    """
    result = run_on_main("interact_with", x, y)
    if AUTO_CHECKPOINT_ENABLED: _auto_checkpoint("interact", f"target=({x},{y})")
    return result

@mcp.tool()
async def execute_battle_turn(action: str) -> str:
    """Executes a high-level battle action."""
    result = run_on_main("execute_battle_turn", action)
    if AUTO_CHECKPOINT_ENABLED: _auto_checkpoint("battle_turn", action)
    return result

@mcp.tool()
async def get_party_info() -> str:
    """Returns a JSON summary of the current party."""
    return run_on_main("get_party_info")

@mcp.tool()
async def read_journal() -> str:
    """Returns a summary of the game journal."""
    return run_on_main("read_journal")

@mcp.tool()
async def write_journal_entry(note: str, metadata: dict = None) -> str:
    """Log a persistent note about the game state."""
    return run_on_main("write_journal_entry", note, metadata)

@mcp.tool()
async def advance_dialogue() -> str:
    """Mashes buttons until the current dialogue box is closed."""
    result = run_on_main("advance_dialogue")
    if AUTO_CHECKPOINT_ENABLED: _auto_checkpoint("dialogue")
    return result

@mcp.tool()
async def get_player_status() -> str:
    """Returns the current Map ID and coordinates."""
    return run_on_main("get_player_status")

@mcp.tool()
async def save_game(name: str = "default") -> str:
    """Saves the current position and state of the game."""
    return run_on_main("save_state", f"saves/{name}.state")

@mcp.tool()
async def load_game(name: str = "default") -> str:
    """Loads a previously saved game state."""
    return run_on_main("load_state", f"saves/{name}.state")

@mcp.tool()
async def press_button(button: str) -> str:
    """Presses a raw button."""
    return run_on_main("press_button", button)

@mcp.tool()
async def wait(seconds: float) -> str:
    """Waits for a number of seconds in game time."""
    return run_on_main("wait", seconds)

@mcp.tool()
async def debug_inspect_tile(x: int, y: int) -> str:
    """DEBUG: Inspect the raw collision byte at map coordinates."""
    return run_on_main("read_map_memory", x, y)

@mcp.tool()
async def add_walkable_collision_byte(byte_hex: str) -> str:
    """Manually add a block ID to the walkable whitelist."""
    return run_on_main("add_walkable_byte", int(byte_hex, 16))

# --- MAIN LOOP ---

def init_emulator(rom_path):
    global emulator, navigation, battle, game_state, vision, collision
    if not os.path.exists(rom_path):
         raise FileNotFoundError(f"ROM file not found at {os.path.abspath(rom_path)}")
    
    headless_env = os.getenv("HEADLESS", "true").lower() == "true"
    print(f"Initializing Emulator (Headless={headless_env})...")
    
    emulator = PokemonEmulator(rom_path, headless=headless_env)
    battle = Battle(emulator)
    collision = CollisionGrid(emulator)
    navigation = Navigation(emulator, collision, battle)
    game_state = GameState(emulator)
    vision = VisionSystem()

def process_command(func_name, args, kwargs):
    try:
        if func_name == "get_screen_analysis":
            img = emulator.screen_image()
            px, py = emulator.get_player_position()
            scx, scy = emulator.get_screen_scroll()
            annotated_img = vision.overlay_grid(img, (px, py), (scx, scy))
            filename = "analysis.png"
            annotated_img.save(filename)
            return True, json.dumps({
                "map_id": emulator.get_map_id(),
                "position": (px, py),
                "image_path": f"{os.getcwd()}/{filename}"
            })
        elif func_name == "get_local_map":
            return True, json.dumps(navigation.get_map_data(*args, **kwargs))
        elif func_name == "walk_to":
            return True, navigation.walk_to(*args, **kwargs)
        elif func_name == "move_direction":
            return True, str(emulator.move_direction(*args, **kwargs))
        elif func_name == "interact_with":
            return True, navigation.interact_with(*args, **kwargs)
        elif func_name == "get_party_info":
            return True, json.dumps(game_state.get_party_info())
        elif func_name == "read_journal":
            return True, json.dumps(game_state.read_journal())
        elif func_name == "write_journal_entry":
            return True, game_state.write_journal_entry(*args, **kwargs)
        elif func_name == "advance_dialogue":
            return True, emulator.advance_dialogue()
        elif func_name == "get_player_status":
            return True, str(navigation.emulator.get_player_position())
        elif func_name == "save_state":
            return True, emulator.save_state(*args, **kwargs)
        elif func_name == "load_state":
            return True, emulator.load_state(*args, **kwargs)
        elif func_name == "press_button":
            emulator.input(args[0])
            return True, f"Pressed {args[0]}"
        elif func_name == "wait":
            emulator.wait(*args, **kwargs)
            return True, "Waited"
        elif func_name == "read_map_memory":
            return True, json.dumps(emulator.read_map_memory(*args, **kwargs))
        elif func_name == "add_walkable_byte":
            collision.add_walkable_byte(args[0])
            return True, "Added"
        elif func_name == "execute_battle_turn":
            return True, battle.execute_action(*args, **kwargs)
        elif func_name == "auto_checkpoint":
            reason, note = args
            save_name = _auto_checkpoint_filename()
            os.makedirs("saves", exist_ok=True)
            path = os.path.join("saves", save_name)
            emulator.save_state(path)
            _prune_auto_checkpoints()
            return True, f"Saved {path}"
    except Exception as e:
        return False, e
    return False, Exception(f"Unknown command: {func_name}")

if __name__ == "__main__":
    try:
        init_emulator("PokemonBlue.gb")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        exit(1)

    threading.Thread(target=lambda: mcp.run(), daemon=True).start()
    print("System Ready.")

    try:
        while True:
            try:
                func_name, args, kwargs = command_queue.get_nowait()
                result = process_command(func_name, args, kwargs)
                response_queue.put(result)
            except queue.Empty:
                pass
            if not emulator.tick(1): break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Stopping...")

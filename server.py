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
from src.vision import VisionSystem

from PIL.Image import Image
import asyncio
import threading
import time

import queue
import json
import datetime
import shutil

# Global Instances
emulator = None
navigation = None
battle = None
game_state = None
vision = None

# Thread-safe Command Queue
command_queue = queue.Queue()
response_queue = queue.Queue()

# Auto-checkpoint config
AUTO_CHECKPOINT_ENABLED = True
AUTO_CHECKPOINT_ACTIONS = {
    "move_direction",
    "interact_with",
    "advance_dialogue",
    "execute_battle_turn",
    "press_buttons",
}

AUTO_SAVE_PREFIX = "auto_"
AUTO_STATE_EXTENSION = ".state"
AUTO_CHECKPOINT_LIMIT = 50
MANUAL_SAVE_BACKUP_SUFFIX = "_backup.state"

def run_on_main(func_name, *args, **kwargs):
    """Sends a command to the main thread and waits for the result."""
    command_queue.put((func_name, args, kwargs))
    # Wait for the response from main thread
    success, result = response_queue.get()
    if not success:
        raise result
    return result

def _auto_checkpoint(reason: str, note: str = ""):
    if not AUTO_CHECKPOINT_ENABLED:
        return None
    return run_on_main("auto_checkpoint", reason, note)

def _rotate_manual_saves(target_name: str):
    """Keep only target + target_backup for manual saves; rotate most recent prior save to backup."""
    _ensure_saves_dir()
    target_file = f"{target_name}.state"
    backup_file = f"{target_name}{MANUAL_SAVE_BACKUP_SUFFIX}"
    existing = []
    for fname in os.listdir("saves"):
        if not fname.endswith(".state"):
            continue
        if fname.startswith(AUTO_SAVE_PREFIX):
            continue
        existing.append(fname)
    if target_file in existing:
        existing.remove(target_file)
    if backup_file in existing:
        existing.remove(backup_file)
    if existing:
        existing.sort(key=lambda f: os.path.getmtime(os.path.join("saves", f)), reverse=True)
        most_recent = existing[0]
        src = os.path.join("saves", most_recent)
        dst = os.path.join("saves", backup_file)
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
        existing = existing[1:]
    for fname in existing:
        os.remove(os.path.join("saves", fname))

def _ensure_saves_dir():
    os.makedirs("saves", exist_ok=True)


def _auto_checkpoint_filename():
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    return f"{AUTO_SAVE_PREFIX}{timestamp}{AUTO_STATE_EXTENSION}"


def _prune_auto_checkpoints():
    _ensure_saves_dir()
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


def _log_save_entry(context: str, filename: str):
    if game_state is None:
        return
    map_id = emulator.get_map_id()
    px, py = emulator.get_player_position()
    entry = f"{context} | map={map_id} pos=({px},{py}) | file={os.path.basename(filename)}"
    game_state.write_journal_entry(entry)

def get_emulator_info():
    """Returns info about the global instances (safe to call from background)."""
    global emulator, navigation, battle, game_state, vision
    return emulator, navigation, battle, game_state, vision

# Updated Tools to use Queue
@mcp.tool()
async def get_screen_analysis() -> str:
    """
    CORE VISION TOOL: Captures the game screen and returns an analysis with a visual grid.
    Returns: JSON with map_id, position, and 'image_path' to the annotated screenshot.
    Use this to 'see' the world, obstacles, and decided where to move.
    """
    return run_on_main("get_screen_analysis")

@mcp.tool()
async def get_local_map() -> str:
    """
    Returns a detailed local map scan including tile IDs, walkability, and nearby objects.
    Useful for debugging collision and navigation issues.
    """
    return run_on_main("get_local_map")

@mcp.tool()
async def get_local_grid(radius: int = 2) -> str:
    """
    Returns a compact square grid around the player with tile metadata.
    radius=2 yields a 5x5 grid centered on the player.
    """
    return run_on_main("get_local_grid", radius)

@mcp.tool()
async def get_tile_histogram(radius: int = 6) -> str:
    """
    Returns counts of tile IDs around the player for quick classification.
    """
    return run_on_main("get_tile_histogram", radius)

@mcp.tool()
async def get_local_grid_ascii(radius: int = 6, show_tid: bool = False, show_walkable: bool = False) -> str:
    """
    Returns a compact ASCII grid centered on the player.
    - show_tid: append hex tile IDs per cell (less compact).
    - show_walkable: append walkability flags per cell.
    """
    return run_on_main("get_local_grid_ascii", radius, show_tid, show_walkable)

@mcp.tool()
async def get_known_warps(map_id: int = None) -> str:
    """
    Returns remembered warps (doors/stairs) for a map ID.
    If map_id is None, uses the current map.
    """
    return run_on_main("get_known_warps", map_id)

@mcp.tool()
async def find_path_to(x: int, y: int, use_memory: bool = False, max_nodes: int = 1000) -> str:
    """
    Returns a planned path and direction list to a target map coordinate.
    If use_memory is True, can path to targets not currently on screen
    using remembered tiles.
    """
    return run_on_main("find_path_to", x, y, use_memory, max_nodes)

@mcp.tool()
async def find_path_to_nearest_warp(use_memory: bool = True, max_nodes: int = 2000) -> str:
    """
    Finds a path to the nearest remembered warp (door/stairs).
    """
    return run_on_main("find_path_to_nearest_warp", use_memory, max_nodes)

# @mcp.tool()
# async def walk_to(x: int, y: int, on_battle: str = "interrupt", avoid_positions: list = None) -> str:
#     """DEPRECATED: Use move_direction sequences based on vision."""
#     return run_on_main("walk_to", x, y, on_battle, avoid_positions)

@mcp.tool()
async def interact_with(x: int, y: int) -> str:
    """
    Interacts with an object at map coordinates (x, y).
    REQUIRED: Use this for Pokéballs on tables, PCs, signs, or talking to stationary people.
    Logic: This tool will automatically walk you to the nearest side of the object and press 'A'.
    """
    result = run_on_main("interact_with", x, y)
    if AUTO_CHECKPOINT_ENABLED:
        _auto_checkpoint("interact", f"target=({x},{y}) result={result}")
    return result

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
    PRIMARY MOVEMENT: Moves the player in a direction.
    - Set `steps` to move a specific distance (e.g., 2 tiles).
    - Set `steps=None` to move until blocked (useful for long corridors).
    Returns: 'arrived', 'blocked', 'transitioned', or 'battle'.
    """
    result = run_on_main("move_direction", direction, steps)
    if AUTO_CHECKPOINT_ENABLED and result != "blocked":
        _auto_checkpoint(f"move_{direction}", f"steps={steps} result={result}")
    return result

@mcp.tool()
async def execute_battle_turn(action: str) -> str:
    """Executes a high-level battle action."""
    result = run_on_main("execute_battle_turn", action)
    if AUTO_CHECKPOINT_ENABLED:
        _auto_checkpoint("battle_turn", f"action={action} result={result}")
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
async def write_journal_entry(note: str) -> str:
    """Log a persistent note about the game state."""
    return run_on_main("write_journal_entry", note)

@mcp.tool()
async def advance_dialogue() -> str:
    """
    REQUIRED: Mashes buttons until the current dialogue box is closed.
    Use this for ALL long conversations, cutscenes, or lectures (like Oak's Intro).
    NEVER use manual press_buttons to progress dialogue as you may lose state context.
    """
    result = run_on_main("advance_dialogue")
    if AUTO_CHECKPOINT_ENABLED:
        _auto_checkpoint("dialogue")
    return result

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
    _rotate_manual_saves(name)
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
    result = run_on_main("press_buttons", sequence)
    if AUTO_CHECKPOINT_ENABLED:
        _auto_checkpoint("buttons", sequence)
    return result

@mcp.tool()
async def walk_to_with_path_check(x: int, y: int, max_steps: int = 100) -> str:
    """
    PRIMARY NAVIGATION: Moves the player to a target, intelligently navigating around unexpected obstacles.
    This tool learns from collisions and recalculates the path.
    Returns: 'arrived', 'blocked', or 'max_steps_reached'.
    """
    result = run_on_main("walk_to_with_path_check", x, y, max_steps)
    if AUTO_CHECKPOINT_ENABLED and result == "arrived":
        _auto_checkpoint("walk_to_with_path_check", f"target=({x},{y}) result={result}")
    return result


def init_emulator(rom_path):
    global emulator, navigation, battle, game_state, vision
    if not os.path.exists(rom_path):
         raise FileNotFoundError(f"ROM file not found at {os.path.abspath(rom_path)}")
    
    headless_env = os.getenv("HEADLESS", "true").lower() == "true"
    print(f"Initializing Emulator (Headless={headless_env})...")
    
    emulator = PokemonEmulator(rom_path, headless=headless_env)
    battle = Battle(emulator)
    navigation = Navigation(emulator, battle)
    game_state = GameState(emulator)
    vision = VisionSystem()

def process_command(func_name, args, kwargs):
    """Executes a command using the global instances (Called on Main Thread)."""
    try:
        if func_name == "get_screen_analysis":
            # Capture and annotate
            img = emulator.screen_image()
            px, py = emulator.get_player_position()
            scx, scy = emulator.get_screen_scroll()
            annotated_img = vision.overlay_grid(img, (px, py), (scx, scy))
            
            filename = "analysis.png"
            annotated_img.save(filename)
            
            return True, json.dumps({
                "map_id": emulator.get_map_id(),
                "position": (px, py),
                "image_path": f"{os.getcwd()}/{filename}",
                "note": "Use the image to identify walls, doors, and NPCs. Grid coords are (x, y)."
            })
        elif func_name == "get_local_map":
            return True, json.dumps(navigation.get_local_map())
        elif func_name == "get_local_grid":
            return True, json.dumps(navigation.get_local_grid(*args, **kwargs))
        elif func_name == "get_tile_histogram":
            return True, json.dumps(navigation.get_tile_histogram(*args, **kwargs))
        elif func_name == "get_local_grid_ascii":
            return True, json.dumps(navigation.get_local_grid_ascii(*args, **kwargs))
        elif func_name == "get_known_warps":
            return True, json.dumps(navigation.get_known_warps(*args, **kwargs))
        elif func_name == "find_path_to":
            return True, json.dumps(navigation.find_path_to(*args, **kwargs))
        elif func_name == "find_path_to_nearest_warp":
            return True, json.dumps(navigation.find_path_to_nearest_warp(*args, **kwargs))
        elif func_name == "get_player_status":
            return True, str(navigation.get_player_status())
        elif func_name == "move_direction":
            result = str(emulator.move_direction(*args, **kwargs))
            return True, result
        elif func_name == "walk_to":
            return True, navigation.walk_to(*args, **kwargs)
        elif func_name == "walk_to_with_path_check":
            return True, navigation.walk_to_with_path_check(*args, **kwargs)
        elif func_name == "interact_with":
            return True, navigation.interact_with(*args, **kwargs)
        elif func_name == "execute_battle_turn":
            return True, battle.execute_action(*args, **kwargs)
        elif func_name == "get_party_info":
            return True, json.dumps(game_state.get_party_info())
        elif func_name == "read_journal":
            return True, json.dumps(game_state.read_journal())
        elif func_name == "read_ram_region":
            return True, str(emulator.read_ram_region(*args, **kwargs))
        elif func_name == "write_journal_entry":
            result = game_state.write_journal_entry(*args, **kwargs)
            return True, result
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
            filename = args[0] if args else kwargs.get("filename")
            result = emulator.save_state(*args, **kwargs)
            if filename:
                _log_save_entry("Manual save", filename)
            return True, result
        elif func_name == "load_state":
            return True, emulator.load_state(*args, **kwargs)
        elif func_name == "auto_checkpoint":
            reason, note = args
            save_name = _auto_checkpoint_filename()
            _ensure_saves_dir()
            file_path = os.path.join("saves", save_name)
            context = f"Checkpoint: {reason}"
            if note:
                context = f"{context} | {note}"
            emulator.save_state(file_path)
            _log_save_entry(context, file_path)
            _prune_auto_checkpoints()
            return True, f"Auto-checkpoint saved to {file_path}"
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

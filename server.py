#!/usr/bin/env python3

from fastmcp import FastMCP
from src.emulator import PokemonEmulator
from src.constants import *
import os
import sys
import signal
import queue
import threading
import time

# Initialize FastMCP Server
mcp = FastMCP("Pokemon Blue Strategy Guide")

# Global Emulator Instance
emulator = None

# Thread-safe Command Queue
command_queue = queue.Queue()
response_queue = queue.Queue()

def run_on_main(func_name, *args, **kwargs):
    command_queue.put((func_name, args, kwargs))
    success, result = response_queue.get()
    if not success:
        raise result
    return result

# --- 5-TOOL MCP INTERFACE ---

@mcp.tool()
async def get_state() -> dict:
    """
    Primary sensory tool.
    Returns clean 4x nearest-neighbor upscaled screenshot ('screen.png'),
    ground-truth tilemap ASCII screen_text, player coordinates, map ID, map name,
    and state flags (in_battle, dialogue_active, menu_active).
    """
    return run_on_main("get_state")

@mcp.tool()
async def step(direction: str, count: int = 1) -> dict:
    """
    Verified cardinal movement across the overworld.
    Arguments:
    - direction: "up", "down", "left", or "right".
    - count: Number of steps to attempt (1 to 10, default 1).

    Halts immediately on obstacles ('hit_obstacle'), battles ('battle_started'),
    warps/doors ('map_transition'), or dialogue ('dialogue_started').
    Returns JSON summarizing steps_completed, final_position, final_map, and interrupted_by.
    """
    return run_on_main("step", direction, count)

@mcp.tool()
async def press(buttons: list[str], delay_frames: int = 15) -> dict:
    """
    Fine-grained button execution for menus, naming, battles, and interactions.
    Arguments:
    - buttons: List of button names (e.g. ["down", "a"], ["start"], ["b"], ["a"]).
    - delay_frames: Frame delay between button presses (default 15 frames / ~250ms).

    Holds each button for 6 frames, ticks delay_frames, then executes the next.
    Returns summary of presses, updated screen_text, and status flags.
    """
    return run_on_main("press", buttons, delay_frames)

@mcp.tool()
async def advance_dialogue(max_pages: int = 5) -> dict:
    """
    Fast-forwards through multi-page NPC speech and cutscenes without losing context.
    Arguments:
    - max_pages: Maximum dialogue pages to clear in one call (default 5).

    Captures each page's text into a transcript before advancing past down-arrows.
    Halts immediately if a choice prompt appears (e.g. YES/NO menu, naming screen, starter selection)
    or if the dialogue box closes.
    Returns JSON with 'pages' array and 'status' ('dialogue_closed' or 'prompt_detected').
    """
    return run_on_main("advance_dialogue", max_pages)

@mcp.tool()
async def save_game(name: str = "default") -> str:
    """Saves the current emulator state checkpoint to saves/<name>.state."""
    return run_on_main("save_game", name)

@mcp.tool()
async def load_game(name: str = "default") -> str:
    """Loads an emulator state checkpoint from saves/<name>.state."""
    return run_on_main("load_game", name)

# --- MAIN LOOP ---

def init_emulator(rom_path):
    global emulator
    if not os.path.exists(rom_path):
        raise FileNotFoundError(f"ROM file not found at {os.path.abspath(rom_path)}")
    
    headless_env = os.getenv("HEADLESS", "true").lower() == "true"
    print(f"Initializing Emulator (Headless={headless_env})...", file=sys.stderr)
    emulator = PokemonEmulator(rom_path, headless=headless_env)

def process_command(func_name, args, kwargs):
    try:
        if func_name == "get_state":
            return True, emulator.get_clean_state()
        elif func_name == "step":
            return True, emulator.step(*args, **kwargs)
        elif func_name == "press":
            return True, emulator.press_sequence(*args, **kwargs)
        elif func_name == "advance_dialogue":
            return True, emulator.advance_dialogue(*args, **kwargs)
        elif func_name == "save_game":
            name = args[0] if args else kwargs.get("name", "default")
            filepath = os.path.join("saves", f"{name}.state")
            return True, emulator.save_state(filepath)
        elif func_name == "load_game":
            name = args[0] if args else kwargs.get("name", "default")
            filepath = os.path.join("saves", f"{name}.state")
            return True, emulator.load_state(filepath)
        else:
            return False, Exception(f"Unknown command: {func_name}")
    except Exception as e:
        return False, e

if __name__ == "__main__":
    def handle_exit(signum, frame):
        os._exit(0)

    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)
    try:
        init_emulator(os.path.join(BASE_DIR, "PokemonBlue.gb"))
    except Exception as e:
        print(f"Failed to initialize: {e}", file=sys.stderr)
        sys.exit(1)

    mcp_thread = threading.Thread(target=lambda: mcp.run(show_banner=False), daemon=True)
    mcp_thread.start()
    print("System Ready.", file=sys.stderr)

    try:
        while True:
            if not mcp_thread.is_alive():
                break
            try:
                func_name, args, kwargs = command_queue.get_nowait()
                result = process_command(func_name, args, kwargs)
                response_queue.put(result)
            except queue.Empty:
                pass
            if not emulator.tick(1):
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping...", file=sys.stderr)
        os._exit(0)

from fastmcp import FastMCP
from src.emulator import PokemonEmulator
from src.constants import *
import os

# Initialize FastMCP
mcp = FastMCP("Pokemon Blue Strategy Guide")

from src.navigation import Navigation
from src.battle import Battle
from src.game_state import GameState

# Global Instances
emulator = None
navigation = None
battle = None
game_state = None

def get_emulator():
    global emulator, navigation, battle, game_state
    if emulator is None:
        rom_path = "PokemonBlue.gb"
        if not os.path.exists(rom_path):
             raise FileNotFoundError(f"ROM file not found at {os.path.abspath(rom_path)}")
        # Check environment variable for headless mode (default: True)
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        emulator = PokemonEmulator(rom_path, headless=headless)
        battle = Battle(emulator)
        navigation = Navigation(emulator, battle)
        game_state = GameState(emulator)
    return emulator, navigation, battle, game_state

@mcp.tool()
def get_local_map() -> str:
    """Returns the current map ID, position, and visual grid."""
    _, nav, _, _ = get_emulator()
    data = nav.get_local_map()
    return str(data)

@mcp.tool()
def walk_to(x: int, y: int, on_battle: str = "interrupt") -> str:
    """
    Moves the player to the target coordinate (x, y).
    on_battle: "interrupt" (default), "run", or "fight".
    Returns the result of the movement.
    """
    _, nav, _, _ = get_emulator()
    result = nav.walk_to(x, y, on_battle)
    return f"Movement result: {result}"

@mcp.tool()
def execute_battle_turn(action: str) -> str:
    """
    Executes a high-level battle action.
    action: "fight_slot_1", "run", "switch_1", etc.
    """
    _, _, bat, _ = get_emulator()
    return bat.execute_action(action)

@mcp.tool()
def get_party_info() -> str:
    """Returns a JSON summary of the current party (Species, HP, Level, Moves)."""
    _, _, _, state = get_emulator()
    data = state.get_party_info()
    return str(data)

@mcp.tool()
def read_journal() -> str:
    """Returns a summary of the game journal."""
    _, _, _, state = get_emulator()
    data = state.read_journal()
    return str(data)

@mcp.tool()
def write_journal_entry(note: str) -> str:
    """Log a persistent note about the game state."""
    _, _, _, state = get_emulator()
    return state.write_journal_entry(note)

if __name__ == "__main__":
    mcp.run()

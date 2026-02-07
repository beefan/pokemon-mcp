from pyboy import PyBoy
import numpy as np
from src.constants import *
import time

class PokemonEmulator:
    def __init__(self, rom_path="PokemonBlue.gb", headless=True):
        self.headless = headless
        self.pyboy = PyBoy(rom_path, window="null" if headless else "SDL2")
        
        if headless:
            self.pyboy.set_emulation_speed(0) # Unlimited for headless
        else:
            self.pyboy.set_emulation_speed(1) # Normal speed for windowed mode
            
    def tick(self, frames=1):
        """Advance the emulator by a number of frames."""
        # When in windowed mode, we need to ensure the OS event loop is processed.
        # pyboy.tick() usually handles this, but a small delay can help stability at high speeds.
        for _ in range(frames):
            if not self.pyboy.tick():
                # If tick returns False, the emulator window was closed.
                return False
        return True
            
    def read_ram(self, address):
        """Read a single byte from RAM."""
        return self.pyboy.memory[address]
    
    def write_ram(self, address, value):
        """Write a single byte to RAM."""
        self.pyboy.memory[address] = value

    def get_player_position(self):
        """Return (x, y) tuple of player coordinates."""
        return (self.read_ram(PLAYER_X), self.read_ram(PLAYER_Y))

    def get_map_id(self):
        """Return the current Map ID."""
        return self.read_ram(MAP_ID_ADDR)

    def get_party_count(self):
        """Return the number of Pokemon in the party."""
        return self.read_ram(PARTY_COUNT_ADDR)

    def read_ram_region(self, start_address, length):
        """Read a range of RAM bytes."""
        return [self.read_ram(start_address + i) for i in range(length)]

    def is_dialogue_active(self):
        """Check if a dialogue box is currently active (0xD11B)."""
        # Some ROM versions or states might not update this perfectly.
        return self.read_ram(0xD11B) != 0
        
    def advance_dialogue(self):
        """Guaranteed mash of A and B for a set number of frames."""
        # Mash for about 2-3 seconds total
        for _ in range(12):
            self.input(BUTTON_A, hold_frames=5)
            self.tick(10)
            self.input(BUTTON_B, hold_frames=5)
            self.tick(10)
            
        # Get immediate feedback for the AI
        new_text = self.get_dialogue_text()
        
        # Safety check: if we see naming screen tiles, warn the AI
        if "lower case" in new_text or "upper case" in new_text or "ED" in new_text:
             return f"WARNING: You are on the NAMING SCREEN. Mashing B deletes characters. New Text:\n{new_text}"
             
        return f"Mashed A/B. New Dialogue Content:\n{new_text}"

    def get_dialogue_text(self):
        """Reads the text currently in the dialogue box area (rows 12-16)."""
        tiles = self.get_screen_tile_ids()
        text_lines = []
        # Indexing is tiles[x][y] in PyBoy
        for y in range(13, 17):
            line = ""
            for x in range(1, 19): 
                tid = tiles[x][y] & 0xFF
                char = TILE_MAP.get(tid, " ")
                line += char
            if line.strip():
                text_lines.append(line.strip())
        return "\n".join(text_lines)

    def get_full_screen_text(self):
        """Scans the entire 20x18 screen for characters."""
        tiles = self.get_screen_tile_ids()
        rows = []
        for y in range(18):
            line = ""
            for x in range(20):
                tid = tiles[x][y] & 0xFF
                line += TILE_MAP.get(tid, " ")
            if line.strip():
                rows.append(line.rstrip())
            else:
                rows.append("") 
        return "\n".join(rows)

    def wait(self, duration_seconds):
        """Waits for a period of time (60 frames per second)."""
        frames = int(duration_seconds * 60)
        self.tick(frames)
        return f"Waited {duration_seconds} seconds."

    def input(self, button, hold_frames=5):
        """Press and release a button."""
        self.pyboy.button_press(button)
        if not self.tick(hold_frames):
            return
        self.pyboy.button_release(button)
        self.tick(5) # Faster gap

    def screen_image(self):
        """Return the current screen image (for visual debugging if needed)."""
        return self.pyboy.screen.image

    def save_state(self, filepath="savegame.state"):
        """Save the current emulator state to a file."""
        with open(filepath, "wb") as f:
            self.pyboy.save_state(f)
        return f"Game state saved to {filepath}"

    def load_state(self, filepath="savegame.state"):
        """Load an emulator state from a file."""
        import os
        if not os.path.exists(filepath):
            return f"Error: Save file {filepath} not found."
        with open(filepath, "rb") as f:
            self.pyboy.load_state(f)
        return f"Game state loaded from {filepath}"

    def get_screen_base64(self):
        """Returns the current screen as a base64 encoded PNG string."""
        from io import BytesIO
        import base64
        img = self.pyboy.screen.image
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def get_screen_tile_ids(self):
        """
        Returns a 20x18 matrix of tile IDs currently visible on screen.
        """
        # pyboy.tilemap_window returns the tile memory indices for the current screen window.
        return self.pyboy.tilemap_window


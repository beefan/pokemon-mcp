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

    def is_dialogue_box_on_screen(self):
        """
        Scans the screen for dialogue box border tiles.
        Standard Gen 1 border tile is 0x79 (Top-Left), 0x7A (Top-Right).
        The dialogue box top border is at row 12.
        """
        try:
            tiles = self.get_screen_tile_ids()
            # Check corners of the dialogue box top row
            tl = tiles[0][12] & 0xFF
            tr = tiles[19][12] & 0xFF
            
            # Common border tile IDs in Pokemon Blue
            # 0xBA is often used for the top border in some versions/palettes
            # 0x7x are standard for others.
            is_border = (tl == tr) and (tl in [0x79, 0xBA, 0x6E])
            
            # Also check if the bottom area is "clean" text tiles (0x7F or 0x80+)
            # instead of world sprites.
            return is_border
        except:
            return False

    def is_dialogue_active(self):
        """Check if a dialogue box is active via RAM OR visual border detection."""
        ram_active = self.read_ram(DIALOGUE_STATE_ADDR) != 0
        visual_active = self.is_dialogue_box_on_screen()
        return ram_active or visual_active
        
    def advance_dialogue(self):
        """Guaranteed mash of A and B for a set number of frames with state verification."""
        # 1. Capture full screen text for robust detection
        full_text = self.get_full_screen_text()
        is_naming_screen = any(k in full_text for k in ["YOUR NAME", "RIVAL'S NAME", "A B C D E", "ED"])
        
        if is_naming_screen:
            return f"CRITICAL STOP: You are on the NAMING SCREEN.\nAction: Use press_buttons('start, wait, a') to accept a default name."

        pre_text = self.get_dialogue_text()
        
        # Mash for about 2-3 seconds total
        for _ in range(12):
            self.input(BUTTON_A, hold_frames=5)
            self.tick(8)
            self.input(BUTTON_B, hold_frames=5)
            self.tick(8)
            
        # 2. PATIENCE BUFFER: Wait an extra half second for scripts to finish
        self.tick(30)
            
        # Check current state (Multi-factor)
        active = self.is_dialogue_active()
        post_text = self.get_dialogue_text()
        full_text_after = self.get_full_screen_text()
        intro_keywords = ["OAK", "NAME", "POKéMON", "WORLD", "ADVENTURE"]
        has_intro_context = any(k in full_text_after for k in intro_keywords)
        
        # Re-check naming screen
        if any(k in full_text_after for k in ["YOUR NAME", "RIVAL'S NAME", "A B C D E", "ED"]):
             return f"STOP: You have reached the NAMING SCREEN.\nAction: Use press_buttons('start, wait, a') to finish naming."

        # Scenario 1: Dialogue is truly closed
        if not active:
            return "STATE CHANGE: Dialogue has CLOSED."

        # Scenario 2: Loop Detection
        if pre_text.strip() == post_text.strip() and len(post_text.strip()) > 0:
            return f"LOOP DETECTED: The text '{post_text.strip()}' has not changed.\nAction: Use walk_to to move away if this is the end of a sequence."
             
        return f"Dialogue Progressing. Content:\n{post_text.strip()}"

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


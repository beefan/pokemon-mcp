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

    def get_screen_scroll(self):
        """Returns the (SCX, SCY) hardware register values."""
        return self.read_ram(SCX_ADDR), self.read_ram(SCY_ADDR)

    def get_party_count(self):
        """Return the number of Pokemon in the party."""
        return self.read_ram(PARTY_COUNT_ADDR)

    def read_ram_region(self, start_address, length):
        """Read a range of RAM bytes."""
        return [self.read_ram(start_address + i) for i in range(length)]

    def is_window_active(self):
        """
        Checks if the hardware Window layer is actually active and visible.
        LCDC Register (0xFF40): Bit 5 enables the Window.
        WY Register (0xFF4A): Window Y position (0-143).
        """
        lcdc = self.read_ram(LCDC_ADDR)
        window_enabled = (lcdc & 0x20) != 0
        wy = self.read_ram(WY_ADDR)
        
        # Window is visible if enabled and Y starts within screen bounds
        # Standard Gen 1 dialogue box has WY=144 (hidden) or WY=104 (row 13).
        return window_enabled and wy < 144

    def is_dialogue_box_on_screen(self):
        """
        Scans the window layer for dialogue box border tiles.
        Only runs if the hardware Window is active.
        """
        if not self.is_window_active():
            return False

        try:
            # For detection, we scan the RAW window tilemap directly
            # to avoid Background interference.
            win_map = self.pyboy.tilemap_window
            
            # Dialogue box top border is usually at row 12 or 13 relative to the Window Y.
            # However, Gen 1 often just keeps it at the bottom of the map.
            tl = win_map[0, 12] & 0xFF
            tr = win_map[19, 12] & 0xFF
            edge = win_map[10, 12] & 0xFF
            
            # Check for corners or a sustained horizontal edge
            is_box = (tl in [0x79, 0xBA, 0x6E] or tr in [0x7A, 0xBA, 0x6E]) or (edge == 0x77)
            return is_box
        except:
            return False

    def is_dialogue_active(self):
        """Check if a dialogue box or naming screen is active."""
        # Battle menus use the Window layer but should not be treated as dialogue.
        if self.is_battle_menu_active():
            return False
        ram_active = self.read_ram(DIALOGUE_STATE_ADDR) != 0
        naming_active = self.read_ram(NAMING_SCREEN_ADDR) != 0
        # Only check visual if the hardware window is on
        visual_active = self.is_dialogue_box_on_screen()
        return ram_active or visual_active or naming_active

    def is_menu_active(self):
        """Returns True when a menu is open (RAM flag)."""
        return self.read_ram(MENU_STATE_ADDR) != 0

    def is_battle_active(self):
        """Returns True when an enemy is present."""
        return self.read_ram(ENEMY_HP_ADDR) > 0

    def is_battle_menu_active(self):
        """
        Heuristic: detect battle menu text on the screen.
        This avoids treating battle menus as dialogue.
        """
        # Avoid heavy scans if not in battle or no window
        if not self.is_battle_active() or not self.is_window_active():
            return False
        full_text = self.get_full_screen_text()
        # Common battle menu labels in Gen 1
        return any(k in full_text for k in ["FIGHT", "PKMN", "ITEM", "RUN"])
        
    def advance_dialogue(self):
        """Guaranteed mash of A and B for a set number of frames with state verification."""
        # 0. STARTUP BUFFER: Give the emulator a few frames to render the box
        # if the tool was called immediately after an interaction.
        self.tick(10)

        # 1. Capture full screen text for robust detection
        full_text = self.get_full_screen_text()
        is_naming_screen = any(k in full_text for k in ["YOUR NAME", "RIVAL'S NAME", "A B C D E", "ED"])
        
        if is_naming_screen:
            return f"CRITICAL STOP: You are on the NAMING SCREEN.\nAction: Use press_buttons('start, wait, a') to accept a default name."

        # Menu guard: do not mash through menus (battle or otherwise).
        if self.is_menu_active() or self.is_battle_menu_active():
            return "STOP: Menu active (battle or system). Use battle tools or manual menu input instead of advance_dialogue."

        pre_text = self.get_dialogue_text()
        
        # 1. Mash and Watch (Stubborn Persistence)
        mash_limit = 12
        total_mashes = 0
        safety_breakout = 100 # Maximum A presses allowed in one tool call
        
        for _ in range(mash_limit):
            # Mash while dialogue is active
            while self.is_dialogue_active():
                if total_mashes >= safety_breakout:
                     return "STOP: ZOMBIE STATE DETECTED. Dialogue box is stuck after 100 mashes. Are you in a menu or a static screen? Try pressing B or moving away."
                
                self.input(BUTTON_A, hold_frames=5)
                self.tick(8)
                self.input(BUTTON_B, hold_frames=5)
                self.tick(8)
                total_mashes += 1
            
            # Dialogue box disappeared. STUBBORN PERSISTENCE: 
            # Wait and watch for 60 frames (1 second) to see if it returns.
            dialogue_returned = False
            for _ in range(30): # Check frequently over 1 second total
                self.tick(2)
                if self.is_dialogue_active():
                    dialogue_returned = True
                    break
            
            if not dialogue_returned:
                # It stayed closed for the full window. We are done!
                break
            # Otherwise, it returned, so the loop continues and we mash again.
            
        # 2. FINAL STABILIZE
        self.tick(15)
            
        # Check current state (Multi-factor)
        active = self.is_dialogue_active()
        post_text = self.get_dialogue_text()
        full_text_after = self.get_full_screen_text()
        
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
        """Reads the text specifically from the Window layer (rows 12-16)."""
        if not self.is_window_active():
            return ""

        # Use raw Window tiles to avoid Background "bleed-through"
        win_map = self.pyboy.tilemap_window
        text_lines = []
        for y in range(13, 17):
            line = ""
            for x in range(1, 19): 
                tid = win_map[x, y] & 0xFF
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

    def move_direction(self, direction, steps=1):
        """
        Moves in the specified direction for a number of steps.
        If steps is None, moves until blocked or a battle starts.
        Returns: "arrived", "blocked", "transitioned", or "battle".
        """
        btn_map = {
            "up": BUTTON_UP,
            "down": BUTTON_DOWN,
            "left": BUTTON_LEFT,
            "right": BUTTON_RIGHT
        }
        button = btn_map.get(direction.lower())
        if not button:
            return f"Error: Invalid direction '{direction}'"

        total_steps = 0
        max_continuous = 100 # Safety limit for None steps
        limit = steps if steps is not None else max_continuous
        
        while total_steps < limit:
            if self.is_dialogue_active():
                return f"stopped: dialogue or menu is active after {total_steps} steps"

            start_x, start_y = self.get_player_position()
            start_map = self.get_map_id()
            
            self.input(button, hold_frames=5)
            # Tick enough for one tile move or transition
            self.tick(15)
            
            end_x, end_y = self.get_player_position()
            end_map = self.get_map_id()
            enemy_hp = self.read_ram(ENEMY_HP_ADDR)

            # Check Termination Conditions
            if enemy_hp > 0:
                return f"battle started after {total_steps + 1} steps"
                
            if start_map != end_map:
                return f"transitioned point reached (Map {end_map}) after {total_steps + 1} steps"

            if (start_x, start_y) == (end_x, end_y):
                # Blocked logic
                if total_steps == 0:
                     # Identify blocker on first fail
                     try:
                        tiles = self.get_screen_tile_ids()
                        tx, ty = 10, 9 # Player center
                        if direction == "up": ty -= 1
                        elif direction == "down": ty += 1
                        elif direction == "left": tx -= 1
                        elif direction == "right": tx += 1
                        
                        tid = tiles[tx][ty] & 0xFF
                        char = TILE_MAP.get(tid, f"ID:0x{tid:02X}")
                        if tid == 0x7F:
                            return "blocked by Invisible Wall / Exit Mat"
                        return f"blocked by {char}"
                     except:
                        return "blocked"
                return f"blocked after {total_steps} steps"
            
            total_steps += 1
            # Brief pause between steps for stability
            self.tick(5)
            
        return f"arrived (moved {total_steps} steps)"

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

    def get_background_tiles(self):
        """
        Returns a 20x18 matrix of tile IDs from the Background layer.
        Accounts for Scroll X (SCX) and Scroll Y (SCY).
        """
        # SCX/SCY are hardware registers in the range 0xFF40-0xFF4B
        scy = self.pyboy.memory[0xFF42]
        scx = self.pyboy.memory[0xFF43]
        
        # Tile coordinates on the 32x32 BG map
        start_tile_x = scx // 8
        start_tile_y = scy // 8
        
        # Get the full 32x32 tilemap IDs
        bg_map = self.pyboy.tilemap_background
        
        matrix = []
        for x in range(20):
            column = []
            for y in range(18):
                # Handle 32x32 wraparound
                tx = (start_tile_x + x) % 32
                ty = (start_tile_y + y) % 32
                column.append(bg_map[tx, ty])
            matrix.append(column)
        return matrix

    def get_window_tiles(self):
        """
        Returns a 20x18 matrix of tile IDs from the Window layer (HUD/Menus).
        """
        # The Window layer is also 32x32, usually shown starting at (0,0) 
        # when active (WY/WX registers control visibility).
        win_map = self.pyboy.tilemap_window
        
        matrix = []
        for x in range(20):
            column = []
            for y in range(18):
                column.append(win_map[x, y])
            matrix.append(column)
        return matrix

    def get_screen_tile_ids(self):
        """
        Returns a 20x18 composite tile ID matrix (Window over Background).
        Accounts for hardware window visibility and position.
        """
        bg = self.get_background_tiles()
        
        if not self.is_window_active():
            return bg

        win = self.get_window_tiles()
        wy = self.read_ram(WY_ADDR)
        wy_tiles = wy // 8
        
        # Composite: Only overlay window tiles where the window is hardware-visible.
        # Gen 1 dialogue box usually has WY=104 (Start row 13).
        composite = []
        for x in range(20):
            column = []
            for y in range(18):
                if y >= wy_tiles:
                    column.append(win[x][y])
                else:
                    column.append(bg[x][y])
            composite.append(column)
        return composite

    def describe_tile(self, screen_x, screen_y):
        """
        Returns a semantic description of the tile at screen coordinates (0-19, 0-17).
        """
        try:
            tiles = self.get_screen_tile_ids()
            tid = tiles[screen_x][screen_y] & 0xFF
            char = TILE_MAP.get(tid, f"ID:0x{tid:02X}")
            name = TILE_NAMES.get(char, "Unknown")
            return f"Tile at ({screen_x}, {screen_y}) is '{char}' ({name})"
        except Exception as e:
            return f"Error describing tile: {e}"

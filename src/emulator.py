import os
import time
from PIL import Image
from pyboy import PyBoy
from src.constants import *

class PokemonEmulator:
    def __init__(self, rom_path="PokemonBlue.gb", headless=True):
        self.headless = headless
        self.pyboy = PyBoy(rom_path, window="null" if headless else "SDL2")
        
        if headless:
            self.pyboy.set_emulation_speed(0)  # Unlimited speed for headless
        else:
            self.pyboy.set_emulation_speed(1)  # Normal speed for windowed mode

    def tick(self, frames=1) -> bool:
        """Advance the emulator by a number of frames."""
        for _ in range(frames):
            if not self.pyboy.tick():
                return False
        return True

    def read_ram(self, address: int) -> int:
        """Read a single byte from RAM."""
        return self.pyboy.memory[address]

    def write_ram(self, address: int, value: int):
        """Write a single byte to RAM."""
        self.pyboy.memory[address] = value

    def get_player_position(self) -> tuple[int, int]:
        """Return (x, y) tuple of player coordinates."""
        return (self.read_ram(PLAYER_X), self.read_ram(PLAYER_Y))

    def get_map_id(self) -> int:
        """Return the current Map ID."""
        return self.read_ram(MAP_ID_ADDR)

    def get_map_name(self) -> str:
        """Return the human-readable map name."""
        map_id = self.get_map_id()
        return MAP_NAMES.get(map_id, f"Map {map_id}")

    def screen_image(self) -> Image.Image:
        """Return the native raw 160x144 screen image as a PIL Image."""
        return self.pyboy.screen.image

    def screen_image_upscaled(self, scale: int = 4) -> Image.Image:
        """Return a clean, upscaled screenshot using nearest-neighbor interpolation."""
        img = self.screen_image()
        new_size = (img.width * scale, img.height * scale)
        return img.resize(new_size, Image.Resampling.NEAREST)

    def get_on_screen_text(self) -> str:
        """
        Extracts clean text currently rendered on the screen from the Game Boy
        engine tilemap buffer (0xC3A0).
        Returns an ASCII string with non-empty rows, or an empty string if no text is shown.
        """
        lines = []
        for y in range(18):
            row_bytes = [self.read_ram(TILEMAP_ADDR + y * 20 + x) for x in range(20)]
            row_str = "".join([CHAR_MAP.get(b, " ") for b in row_bytes]).rstrip()
            if row_str.strip():
                lines.append(row_str)
        return "\n".join(lines)

    def get_dialogue_page_text(self) -> str:
        """Reads text lines from rows 13-16 of the dialogue box in wTileMap."""
        lines = []
        for y in range(13, 17):
            row_bytes = [self.read_ram(TILEMAP_ADDR + y * 20 + x) for x in range(1, 19)]
            s = "".join([CHAR_MAP.get(b, " ") for b in row_bytes]).strip()
            s = s.replace("▼", "").rstrip()
            if s:
                lines.append(s)
        return "\n".join(lines)

    def is_window_active(self) -> bool:
        """
        Checks if the hardware Window layer is active and within screen bounds.
        LCDC Register (0xFF40): Bit 5 enables the Window.
        WY Register (0xFF4A): Window Y position (0-143).
        """
        lcdc = self.read_ram(LCDC_ADDR)
        window_enabled = (lcdc & 0x20) != 0
        wy = self.read_ram(WY_ADDR)
        return window_enabled and wy < 144

    def is_dialogue_box_on_screen(self) -> bool:
        """
        Checks if standard dialogue box borders are present in the tilemap buffer.
        Standard Gen 1 dialogue box has top border at row 12 and bottom border at row 17.
        """
        top_left = self.read_ram(TILEMAP_ADDR + 12 * 20)
        top_right = self.read_ram(TILEMAP_ADDR + 12 * 20 + 19)
        bot_left = self.read_ram(TILEMAP_ADDR + 17 * 20)
        bot_right = self.read_ram(TILEMAP_ADDR + 17 * 20 + 19)
        return (top_left == 0x79 or top_right == 0x7B) and (bot_left == 0x7D or bot_right == 0x7E)

    def is_battle_active(self) -> bool:
        """Returns True when an enemy is present in combat."""
        return self.read_ram(ENEMY_HP_ADDR) > 0

    def is_battle_menu_active(self) -> bool:
        """Detects if the in-battle action menu (FIGHT/PKMN/ITEM/RUN) is open."""
        if not self.is_battle_active():
            return False
        screen_text = self.get_on_screen_text()
        return any(k in screen_text for k in ["FIGHT", "PKMN", "ITEM", "RUN"])

    def is_menu_active(self) -> bool:
        """Returns True when a start menu, choice prompt, or battle menu is active."""
        if self.read_ram(MENU_WATCHED_KEYS_ADDR) != 0:
            return True
        if self.read_ram(MENU_STATE_ADDR) != 0:
            return True
        if self.is_battle_menu_active():
            return True
        text = self.get_on_screen_text()
        # Menu cursor ▶ is present while not inside a dialogue speech box
        if "▶" in text and not self.is_dialogue_box_on_screen():
            return True
        return False

    def is_dialogue_active(self) -> bool:
        """Checks if dialogue or cutscene text is active and waiting or progressing."""
        if self.is_menu_active() or self.is_battle_menu_active():
            return False
        if self.read_ram(DIALOGUE_STATE_ADDR) != 0:
            return True
        if self.read_ram(NAMING_SCREEN_ADDR) != 0:
            return True
        if self.is_dialogue_box_on_screen():
            return True
        return False

    def get_clean_state(self, save_path: str = "screen.png") -> dict:
        """
        Primary sensory method.
        Saves a 4x nearest-neighbor upscaled screenshot (640x576) and returns
        visual text, position, map, and status flags.
        """
        upscaled = self.screen_image_upscaled(scale=4)
        abs_path = os.path.abspath(save_path)
        upscaled.save(abs_path)

        map_id = self.get_map_id()
        map_name = MAP_NAMES.get(map_id, f"Map {map_id}")
        pos = list(self.get_player_position())
        screen_text = self.get_on_screen_text()
        in_battle = self.is_battle_active()
        dialogue_active = self.is_dialogue_active()
        menu_active = self.is_menu_active()

        return {
            "image_path": abs_path,
            "screen_text": screen_text,
            "map_id": map_id,
            "map_name": map_name,
            "position": pos,
            "in_battle": in_battle,
            "dialogue_active": dialogue_active,
            "menu_active": menu_active,
        }

    def step(self, direction: str, count: int = 1) -> dict:
        """
        Executes verified cardinal movement across the overworld.
        Respects 16-frame movement grid and turn delay.
        Halts immediately on obstacles, battles, warps, or dialogue triggers.
        """
        d_clean = direction.lower().strip()
        btn_map = {
            "up": BUTTON_UP,
            "down": BUTTON_DOWN,
            "left": BUTTON_LEFT,
            "right": BUTTON_RIGHT,
        }
        if d_clean not in btn_map:
            raise ValueError(f"Invalid direction '{direction}'. Must be 'up', 'down', 'left', or 'right'.")

        count = max(1, min(10, count))
        btn = btn_map[d_clean]
        steps_completed = 0
        interrupted_by = None

        for _ in range(count):
            # Pre-step checks
            if self.is_battle_active():
                interrupted_by = "battle_started"
                break
            if self.is_dialogue_active():
                interrupted_by = "dialogue_started"
                break

            start_pos = self.get_player_position()
            start_map = self.get_map_id()

            # Execute step: hold button for 8 frames, tick 16 frames for standard grid step
            self.pyboy.button_press(btn)
            self.tick(8)
            self.pyboy.button_release(btn)
            self.tick(16)

            end_pos = self.get_player_position()
            end_map = self.get_map_id()

            # Post-step checks
            if self.is_battle_active():
                steps_completed += 1
                interrupted_by = "battle_started"
                break

            if end_map != start_map:
                steps_completed += 1
                interrupted_by = "map_transition"
                # Allow warp transition to fully complete (screen fade-out, map load, and fade-in)
                self.tick(60)
                break

            if self.is_dialogue_active():
                steps_completed += 1
                interrupted_by = "dialogue_started"
                break

            if end_pos == start_pos:
                interrupted_by = "hit_obstacle"
                break

            steps_completed += 1

        final_map_id = self.get_map_id()
        final_map_name = MAP_NAMES.get(final_map_id, f"Map {final_map_id}")

        return {
            "steps_completed": steps_completed,
            "final_position": list(self.get_player_position()),
            "final_map": final_map_name,
            "map_id": final_map_id,
            "interrupted_by": interrupted_by,
        }

    def press_sequence(self, buttons: list[str], delay_frames: int = 15) -> dict:
        """
        Executes fine-grained button presses with delays for menus, naming, battles, and interactions.
        Holds each button for 6 frames, ticks delay_frames, then executes the next.
        """
        btn_map = {
            "a": BUTTON_A,
            "b": BUTTON_B,
            "start": BUTTON_START,
            "select": BUTTON_SELECT,
            "up": BUTTON_UP,
            "down": BUTTON_DOWN,
            "left": BUTTON_LEFT,
            "right": BUTTON_RIGHT,
        }
        executed = []
        for b in buttons:
            b_clean = b.lower().strip()
            if b_clean not in btn_map:
                raise ValueError(f"Invalid button '{b}'. Valid buttons are: {list(btn_map.keys())}")
            btn = btn_map[b_clean]
            self.pyboy.button_press(btn)
            self.tick(6)
            self.pyboy.button_release(btn)
            self.tick(delay_frames)
            executed.append(b_clean)

        return {
            "presses": executed,
            "screen_text": self.get_on_screen_text(),
            "in_battle": self.is_battle_active(),
            "dialogue_active": self.is_dialogue_active(),
            "menu_active": self.is_menu_active(),
        }

    def advance_dialogue(self, max_pages: int = 5) -> dict:
        """
        Fast-forwards through multi-page NPC speech and cutscenes without losing context.
        Captures each page's text into a transcript before advancing.
        Halts immediately if a choice prompt appears or if the dialogue box closes.
        """
        # Startup buffer: wait up to 30 frames for a dialogue box or prompt if called right after interaction
        for _ in range(15):
            wTileMap = [self.read_ram(TILEMAP_ADDR + i) for i in range(360)]
            if (self.read_ram(TILEMAP_ADDR + 12 * 20) == 0x79) or (0xED in wTileMap):
                break
            self.tick(2)

        pages = []
        status = "dialogue_closed"

        for _ in range(max_pages):
            page_captured = False
            for _ in range(200):
                self.tick(2)
                wTileMap = [self.read_ram(TILEMAP_ADDR + i) for i in range(360)]

                # Check for choice prompt (cursor ▶)
                if 0xED in wTileMap:
                    status = "prompt_detected"
                    page_text = self.get_dialogue_page_text()
                    if page_text and (not pages or pages[-1] != page_text):
                        pages.append(page_text)
                    return {"pages": pages, "status": status}

                # Check if dialogue box is open
                has_box = (self.read_ram(TILEMAP_ADDR + 12 * 20) == 0x79)
                if not has_box:
                    # Give it a few frames to see if it re-opens (page transition)
                    reopened = False
                    for _ in range(20):
                        self.tick(2)
                        if self.read_ram(TILEMAP_ADDR + 12 * 20) == 0x79:
                            reopened = True
                            break
                    if not reopened:
                        status = "dialogue_closed"
                        return {"pages": pages, "status": status}

                # Check for down arrow (0xEE)
                if 0xEE in wTileMap:
                    page_text = self.get_dialogue_page_text()
                    if page_text and (not pages or pages[-1] != page_text):
                        pages.append(page_text)
                    self.pyboy.button_press(BUTTON_A)
                    self.tick(6)
                    self.pyboy.button_release(BUTTON_A)
                    self.tick(10)
                    page_captured = True
                    break
                else:
                    # Accelerate text typing with A
                    self.pyboy.button_press(BUTTON_A)
                    self.tick(2)
                    self.pyboy.button_release(BUTTON_A)

            if not page_captured:
                break

        has_box = (self.read_ram(TILEMAP_ADDR + 12 * 20) == 0x79)
        return {"pages": pages, "status": "dialogue_closed" if not has_box else "prompt_detected" if (0xED in [self.read_ram(TILEMAP_ADDR + i) for i in range(360)]) else "dialogue_closed"}

    def save_state(self, filepath: str = "saves/savegame.state") -> str:
        """Save the current emulator state to a file."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "wb") as f:
            self.pyboy.save_state(f)
        return f"Game state saved to {filepath}"

    def load_state(self, filepath: str = "saves/savegame.state") -> str:
        """Load an emulator state from a file."""
        if not os.path.exists(filepath):
            return f"Error: Save file {filepath} not found."
        with open(filepath, "rb") as f:
            self.pyboy.load_state(f)
        self.tick(5)  # Stabilization frames
        return f"Game state loaded from {filepath}"

from pyboy import PyBoy
import numpy as np
from src.constants import *
import time

class PokemonEmulator:
    def __init__(self, rom_path="PokemonBlue.gb", headless=True):
        self.pyboy = PyBoy(rom_path, window="null" if headless else "SDL2")
        self.pyboy.set_emulation_speed(0) # Unlimited speed for fast processing
        
    def tick(self, frames=1):
        """Advance the emulator by a number of frames."""
        for _ in range(frames):
            self.pyboy.tick()
            
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
        
    def input(self, button, hold_frames=5):
        """Press and release a button."""
        self.pyboy.button_press(button)
        self.tick(hold_frames)
        self.pyboy.button_release(button)
        self.tick(1)

    def screen_image(self):
        """Return the current screen image (for visual debugging if needed)."""
        return self.pyboy.screen_image()

    def get_screen_tile_ids(self):
        """
        Returns a 20x18 matrix of tile IDs currently visible on screen.
        """
        # pyboy.tilemap_window returns the tile memory indices for the current screen window.
        return self.pyboy.tilemap_window


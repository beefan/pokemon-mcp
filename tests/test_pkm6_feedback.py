import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.emulator import PokemonEmulator
from src.constants import *

class TestPKM6Feedback(unittest.TestCase):
    def setUp(self):
        # Mock PyBoy
        self.patcher = patch('src.emulator.PyBoy')
        self.MockPyBoy = self.patcher.start()
        # Initialize emulator with dummy ROM path
        self.emulator = PokemonEmulator(rom_path="PokemonBlue.gb", headless=True)
        
    def tearDown(self):
        self.patcher.stop()

    def test_move_direction_blocked_after_steps(self):
        # Setup: Player at (10, 10), moves 1 step to (11, 10), then blocked at (12, 10)
        def ram_side_effect(addr):
            # First call (total_steps=0): at (10,10)
            if self.emulator.read_ram.call_count <= 8: # Arbitrary count for first iteration setup
                if addr == PLAYER_X: return 10
                if addr == PLAYER_Y: return 10
            # Second call (total_steps=1): at (11,10)
            else:
                if addr == PLAYER_X: return 11
                if addr == PLAYER_Y: return 11
            
            if addr == MAP_ID_ADDR: return 0
            if addr == ENEMY_HP_ADDR: return 0
            if addr == DIALOGUE_STATE_ADDR: return 0
            if addr == NAMING_SCREEN_ADDR: return 0
            if addr == MENU_STATE_ADDR: return 0
            if addr == MAP_WIDTH_ADDR: return 20
            return 0
            
        self.emulator.read_ram = MagicMock(side_effect=ram_side_effect)
        
        # Mock read_map_memory for (12, 10)
        self.emulator.read_map_memory = MagicMock(return_value={
            "collision_byte": "0x55",
            "is_walkable": False
        })
        
        # Mock screen tiles (Tile ID 0x05 is '#' / Wall)
        mock_tiles = [[0x00 for _ in range(18)] for _ in range(20)]
        mock_tiles[11][9] = 0x05 # Wall at (12, 10) relative to player at (11, 10)
        self.emulator.get_screen_tile_ids = MagicMock(return_value=mock_tiles)
        
        # Attempt to move RIGHT 2 steps
        result = self.emulator.move_direction("right", steps=2)
        
        self.assertIn("blocked by #", result)
        self.assertIn("after 1 steps", result)
        self.assertIn("collision_byte=0x55", result)

    def test_move_direction_blocked_by_npc(self):
        # Setup: Player at (10, 10), NPC at (10, 9)
        # Mock RAM
        def ram_side_effect(addr):
            if addr == PLAYER_X: return 10
            if addr == PLAYER_Y: return 10
            if addr == MAP_ID_ADDR: return 0
            if addr == ENEMY_HP_ADDR: return 0
            if addr == DIALOGUE_STATE_ADDR: return 0
            if addr == NAMING_SCREEN_ADDR: return 0
            if addr == MAP_WIDTH_ADDR: return 20
            if addr == MENU_STATE_ADDR: return 0
            # Mock NPC in slot 1 at (10, 9)
            # $C100 + (1 * 0x10) = 0xC110
            if addr == 0xC110: return 1 # Active
            if addr == 0xC110 + 4: return 9 + 4 # Y coord (offset by 4)
            if addr == 0xC110 + 6: return 10 + 4 # X coord (offset by 4)
            return 0
            
        self.emulator.read_ram = MagicMock(side_effect=ram_side_effect)
        
        # Mock read_map_memory
        self.emulator.read_map_memory = MagicMock(return_value={
            "collision_byte": "0x01",
            "is_walkable": False
        })
        
        # Attempt to move UP (towards (10, 9))
        result = self.emulator.move_direction("up")
        
        self.assertEqual(result, "blocked by NPC at (10, 9)")

    def test_move_direction_blocked_by_wall_with_byte(self):
        # Setup: Player at (10, 10), Wall at (11, 10)
        def ram_side_effect(addr):
            if addr == PLAYER_X: return 10
            if addr == PLAYER_Y: return 10
            if addr == MAP_ID_ADDR: return 0
            if addr == ENEMY_HP_ADDR: return 0
            if addr == DIALOGUE_STATE_ADDR: return 0
            if addr == NAMING_SCREEN_ADDR: return 0
            if addr == MENU_STATE_ADDR: return 0
            if addr == 0xFF40: return 0 # No window
            if addr == MAP_WIDTH_ADDR: return 20
            # No NPCs
            return 0
            
        self.emulator.read_ram = MagicMock(side_effect=ram_side_effect)
        
        # Mock read_map_memory for (11, 10)
        self.emulator.read_map_memory = MagicMock(return_value={
            "collision_byte": "0xFF",
            "is_walkable": False
        })
        
        # Mock screen tiles (Tile ID 0x05 is '#' / Wall)
        # Center is (10, 9) on screen
        mock_tiles = [[0x00 for _ in range(18)] for _ in range(20)]
        # For direction "right", we check (11, 9)
        mock_tiles[11][9] = 0x05
        self.emulator.get_screen_tile_ids = MagicMock(return_value=mock_tiles)
        
        # Attempt to move RIGHT
        result = self.emulator.move_direction("right")
        
        self.assertIn("blocked by #", result)
        self.assertIn("collision_byte=0xFF", result)

if __name__ == '__main__':
    unittest.main()

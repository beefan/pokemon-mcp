import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.navigation import Navigation
from src.collision import CollisionGrid
from src.constants import *

class TestPKM12Directional(unittest.TestCase):
    def setUp(self):
        self.emulator = MagicMock()
        self.collision = CollisionGrid(self.emulator)
        self.nav = Navigation(self.emulator, self.collision)
        
    def test_ledge_walkability(self):
        # 0x36 is South Ledge (only allowed to exit DOWN)
        # Wait, the bitmask is "Allowed Exit Directions". 
        # So if I am AT (10, 10) and it is 0x36, I can only move DOWN.
        
        self.collision.walkable_masks[0x36] = DIR_DOWN
        
        # Mock map width 20
        self.emulator.read_ram.return_value = 20 # Map Width
        
        # Mocking read_ram for is_walkable is tricky because it calculates address.
        # stride = 26. offset = (y+3)*26 + (x+3).
        # To make it easy, I'll patch the memory read.
        
        def fake_ram(addr):
            if addr == MAP_WIDTH_ADDR: return 20
            # Let's say (10, 10) has the ledge
            # stride = 26. offset = 13 * 26 + 13 = 338 + 13 = 351.
            # COLLISION_MAP_START_ADDR + 351
            if addr == COLLISION_MAP_START_ADDR + 351:
                return 0x36
            return 0x00 # Standard floor elsewhere
            
        self.emulator.read_ram.side_effect = fake_ram
        
        # Test 1: Entering the ledge from North (moving DOWN)
        # Wait, the ledge Tile is at (10, 10).
        # Gen 1 Ledges: You jump OVER them.
        # Actually, in Gen 1, the Ledge TILE itself is what you click to jump.
        # So if I am at (10, 9) and I move DOWN, I step on (10, 10).
        # My logic check `mask & from_direction` checks the mask of the TARGET tile?
        # Let's re-read the implementation.
        # `is_walkable(x, y, from_direction=mask)` checks if tile (x, y) can be entered/exited in that direction.
        # If (10, 10) has DIR_DOWN, it means you can ONLY move DOWN while on/into it?
        # Actually, it's safer to say the Ledge tile ALLOWS movement in the jump direction only.
        
        # From North (10, 9) to (10, 10) is a DOWN move.
        self.assertTrue(self.collision.is_walkable(10, 10, from_direction=DIR_DOWN), 
                        "Should allow moving DOWN onto/over South Ledge")
        
        # From South (10, 11) to (10, 10) is an UP move.
        self.assertFalse(self.collision.is_walkable(10, 10, from_direction=DIR_UP), 
                         "Should NOT allow moving UP onto South Ledge")

    def test_pathfinding_respects_ledge(self):
        self.collision.walkable_masks[0x36] = DIR_DOWN
        
        def fake_ram(addr):
            if addr == MAP_WIDTH_ADDR: return 20
            # Row of ledges at Y=10
            # (9, 10), (10, 10), (11, 10) are all 0x36
            # stride 26. (10 + 3) * 26 + (x + 3)
            # x=9: 13*26 + 12 = 338+12 = 350
            # x=10: 13*26 + 13 = 351
            # x=11: 13*26 + 14 = 352
            if addr in (COLLISION_MAP_START_ADDR+350, COLLISION_MAP_START_ADDR+351, COLLISION_MAP_START_ADDR+352):
                return 0x36
            return 0x00 # Floor
            
        self.emulator.read_ram.side_effect = fake_ram
        
        # Path from (10, 9) to (10, 11) - moving DOWN. Should go straight.
        path = self.nav.find_path((10, 9), (10, 11))
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (10, 10))
        
        # Path from (10, 11) to (10, 9) - moving UP. Should avoid the ledge.
        # If the ledge is a wall for UP moves, it should find a path around it (e.g. via x=8 or x=12)
        path = self.nav.find_path((10, 11), (10, 9))
        self.assertIsNotNone(path)
        for pos in path:
            self.assertNotEqual(pos, (10, 10), "Path should not go UP onto a South ledge")
            self.assertNotEqual(pos, (9, 10))
            self.assertNotEqual(pos, (11, 10))

if __name__ == '__main__':
    unittest.main()

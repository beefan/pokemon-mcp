import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.collision import CollisionGrid
from src.constants import WALKABLE_BLOCK_IDS, MAP_WIDTH_ADDR, COLLISION_MAP_START_ADDR

class TestCollisionGridDynamic(unittest.TestCase):
    def test_dynamic_whitelist(self):
        # Mock emulator
        mock_emulator = MagicMock()
        
        # Initialize CollisionGrid
        collision = CollisionGrid(mock_emulator)
        
        # Verify initial state matches constants
        self.assertEqual(collision.walkable_ids, WALKABLE_BLOCK_IDS)
        
        # Pick a byte that is definitely NOT walkable (e.g. 0xFF)
        blocked_byte = 0xFF
        self.assertNotIn(blocked_byte, WALKABLE_BLOCK_IDS)
        
        # Setup mock to return this blocked byte for a specific tile
        # We need to mock read_ram for map width and the collision byte
        def side_effect(addr):
            if addr == MAP_WIDTH_ADDR:
                return 10 # Width 10
            # For simplicity, make all collision lookups return blocked_byte
            return blocked_byte
            
        mock_emulator.read_ram.side_effect = side_effect
        
        # Verify is_walkable returns False initially
        self.assertFalse(collision.is_walkable(5, 5))
        
        # Learn the byte
        collision.add_walkable_byte(blocked_byte)
        
        # Verify byte is now in whitelist
        self.assertIn(blocked_byte, collision.walkable_ids)
        
        # Verify is_walkable now returns True
        self.assertTrue(collision.is_walkable(5, 5))

if __name__ == '__main__':
    unittest.main()

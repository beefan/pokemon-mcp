import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.navigation import Navigation
from src.constants import *

class TestPKM7Interact(unittest.TestCase):
    def setUp(self):
        self.emulator = MagicMock()
        self.collision = MagicMock()
        self.nav = Navigation(self.emulator, self.collision)
        
    def test_interaction_dialogue_started(self):
        # Setup pre-state
        self.emulator.get_map_id.return_value = 0
        self.emulator.get_player_position.return_value = (10, 10)
        self.emulator.is_dialogue_active.side_effect = [False, True] # Pre, then Post
        
        # Target at (10, 9), player at (10, 10) is already adjacent
        self.nav._adjacent_walkable_positions = MagicMock(return_value=[(10, 10, "up")])
        self.nav._get_collision_tile = MagicMock(return_value={"char": " ", "tid": 0x01, "walkable": True})
        
        result = self.nav.interact_with(10, 9)
        self.assertEqual(result, "interaction_success: dialogue_started")

    def test_interaction_map_changed(self):
        # Setup pre-state
        self.emulator.get_map_id.side_effect = [0, 40] # Pre, then Post
        self.emulator.get_player_position.return_value = (10, 10)
        self.emulator.is_dialogue_active.return_value = False
        
        self.nav._adjacent_walkable_positions = MagicMock(return_value=[(10, 10, "up")])
        
        result = self.nav.interact_with(10, 9)
        self.assertEqual(result, "interaction_success: map_changed to 40")

    def test_interaction_door_hint(self):
        # Setup pre-state: No changes detected
        self.emulator.get_map_id.return_value = 0
        self.emulator.get_player_position.return_value = (10, 10)
        self.emulator.is_dialogue_active.return_value = False
        
        self.nav._adjacent_walkable_positions = MagicMock(return_value=[(10, 10, "up")])
        
        # Target is a door
        self.nav._get_collision_tile = MagicMock(return_value={"char": ">", "tid": 0x3E, "walkable": True})
        
        result = self.nav.interact_with(10, 9)
        self.assertIn("interaction_failed", result)
        self.assertIn("step-on warp", result)
        self.assertIn("door", result)

    def test_interaction_stairs_hint(self):
        # Setup pre-state: No changes detected
        self.emulator.get_map_id.return_value = 0
        self.emulator.get_player_position.return_value = (10, 10)
        self.emulator.is_dialogue_active.return_value = False
        
        self.nav._adjacent_walkable_positions = MagicMock(return_value=[(10, 10, "up")])
        
        # Target is stairs
        self.nav._get_collision_tile = MagicMock(return_value={"char": "S", "tid": 0x15, "walkable": True})
        
        result = self.nav.interact_with(10, 9)
        self.assertIn("interaction_failed", result)
        self.assertIn("step-on warp", result)
        self.assertIn("stairs", result)

if __name__ == '__main__':
    unittest.main()

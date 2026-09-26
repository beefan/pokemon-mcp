import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import MAP_NAMES, CHAR_MAP, BUTTON_A, BUTTON_START
from src.emulator import PokemonEmulator

class TestEmulatorUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.emulator = PokemonEmulator(rom_path="PokemonBlue.gb", headless=True)
        # Tick a few frames to boot
        cls.emulator.tick(30)

    def test_constants_coverage(self):
        # 248 Gen 1 maps mapped
        self.assertGreaterEqual(len(MAP_NAMES), 248)
        self.assertEqual(MAP_NAMES[0], "Pallet Town")
        self.assertEqual(MAP_NAMES[1], "Viridian City")
        self.assertEqual(MAP_NAMES[12], "Route 1")
        self.assertEqual(MAP_NAMES[37], "Player's House 1F")
        self.assertEqual(MAP_NAMES[38], "Player's House 2F")
        self.assertEqual(MAP_NAMES[40], "Oak's Lab")

        # CHAR_MAP contains essential UI and alpha characters
        self.assertEqual(CHAR_MAP[0x80], "A")
        self.assertEqual(CHAR_MAP[0xA0], "a")
        self.assertEqual(CHAR_MAP[0xF6], "0")
        self.assertEqual(CHAR_MAP[0xED], "▶")
        self.assertEqual(CHAR_MAP[0xEE], "▼")

    def test_get_clean_state_structure(self):
        state = self.emulator.get_clean_state("scratch_unit_test.png")
        expected_keys = [
            "image_path", "screen_text", "map_id", "map_name",
            "position", "in_battle", "dialogue_active", "menu_active"
        ]
        for key in expected_keys:
            self.assertIn(key, state)
        self.assertTrue(os.path.exists(state["image_path"]))
        self.assertIsInstance(state["position"], list)
        self.assertEqual(len(state["position"]), 2)
        self.assertIsInstance(state["in_battle"], bool)
        self.assertIsInstance(state["dialogue_active"], bool)
        self.assertIsInstance(state["menu_active"], bool)
        if os.path.exists("scratch_unit_test.png"):
            os.remove("scratch_unit_test.png")

    def test_press_sequence(self):
        # Valid button sequence
        res = self.emulator.press_sequence(["start"], delay_frames=5)
        self.assertEqual(res["presses"], ["start"])
        self.assertIn("screen_text", res)
        self.assertIn("in_battle", res)
        self.assertIn("dialogue_active", res)
        self.assertIn("menu_active", res)

        # Invalid button raises ValueError
        with self.assertRaises(ValueError):
            self.emulator.press_sequence(["invalid_btn"])

    def test_step_invalid_direction(self):
        with self.assertRaises(ValueError):
            self.emulator.step("diagonal", count=1)

    def test_save_and_load_state(self):
        save_path = "saves/test_unit_save.state"
        save_msg = self.emulator.save_state(save_path)
        self.assertIn("saved to", save_msg)
        self.assertTrue(os.path.exists(save_path))

        load_msg = self.emulator.load_state(save_path)
        self.assertIn("loaded from", load_msg)

        if os.path.exists(save_path):
            os.remove(save_path)

if __name__ == "__main__":
    unittest.main()

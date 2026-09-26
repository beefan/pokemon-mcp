import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import *
from src.emulator import PokemonEmulator

class TestArrivalIntegration(unittest.TestCase):
    def test_full_boot_to_pallet_town_arrival(self):
        """
        End-to-End Integration Test:
        Proves that the 5 refactored tools can:
        1. Read state and text on boot via get_clean_state().
        2. Select a name on the naming screen via advance_dialogue() and press_sequence().
        3. Clear Oak's cutscene via advance_dialogue().
        4. Move from bedroom (Map 38) downstairs to 1F (Map 37) via step().
        5. Exit 1F to Pallet Town (Map 0) via step().
        """
        emu = PokemonEmulator(rom_path="PokemonBlue.gb", headless=True)

        # 1. Boot up: verify initial sensory state
        state = emu.get_clean_state("scratch_boot_test.png")
        self.assertIsNotNone(state["image_path"])
        self.assertTrue(os.path.exists(state["image_path"]))
        self.assertIn("map_id", state)
        self.assertIn("screen_text", state)

        # Skip intro animation to Title Screen (press START)
        for _ in range(12):
            emu.tick(60)
            emu.press_sequence(["start"], delay_frames=4)

        # Title menu: Select NEW GAME with 'A'
        emu.press_sequence(["a"], delay_frames=60)

        # 2. Advance dialogue through Oak's intro to player naming prompt
        prompt_found = False
        for _ in range(10):
            res = emu.advance_dialogue(max_pages=5)
            if res["status"] == "prompt_detected":
                prompt_found = True
                break
        self.assertTrue(prompt_found, "Failed to reach player naming prompt")

        # Verify naming prompt in screen text
        naming_state = emu.get_clean_state()
        self.assertIn("▶", naming_state["screen_text"])

        # Pick default name 'BLUE': Down then A
        emu.press_sequence(["down", "a"], delay_frames=20)

        # Advance dialogue to rival naming prompt
        rival_prompt_found = False
        for _ in range(10):
            res = emu.advance_dialogue(max_pages=5)
            if res["status"] == "prompt_detected":
                rival_prompt_found = True
                break
        self.assertTrue(rival_prompt_found, "Failed to reach rival naming prompt")

        # Pick default rival name 'RED': Down then A
        emu.press_sequence(["down", "a"], delay_frames=20)

        # 3. Clear Oak's final cutscenes into the bedroom (Map 38)
        # Advance dialogue segments separated by animations
        all_pages = []
        for _ in range(10):
            emu.tick(30)
            res = emu.advance_dialogue(max_pages=5)
            all_pages.extend(res["pages"])
            if res["status"] == "dialogue_closed" and len(res["pages"]) == 0 and not emu.is_dialogue_box_on_screen():
                break

        # Wait for overworld fade-in to complete
        for _ in range(60):
            emu.tick(2)

        # Verify Bedroom arrival state
        bed_state = emu.get_clean_state("scratch_bedroom_verified.png")
        self.assertEqual(bed_state["map_id"], 38)
        self.assertEqual(bed_state["map_name"], "Player's House 2F")
        self.assertEqual(bed_state["position"], [3, 6])
        self.assertFalse(bed_state["dialogue_active"])
        self.assertFalse(bed_state["in_battle"])
        self.assertFalse(bed_state["menu_active"])

        # 4. Move from Bedroom (3, 6) across to stairs at (7, 1)
        # From (3, 6): Move right 2 steps to (5, 6)
        r_step = emu.step("right", count=2)
        self.assertEqual(r_step["steps_completed"], 2)
        self.assertEqual(r_step["final_position"], [5, 6])

        # Move up 5 steps to (5, 1)
        u_step = emu.step("up", count=5)
        self.assertEqual(u_step["steps_completed"], 5)
        self.assertEqual(u_step["final_position"], [5, 1])

        # Move right 2 steps: steps onto stairs at (7, 1) -> Warps to Map 37 (1F)!
        warp_step = emu.step("right", count=2)
        self.assertEqual(warp_step["interrupted_by"], "map_transition")
        self.assertEqual(emu.get_map_id(), 37)
        self.assertEqual(emu.get_map_name(), "Player's House 1F")

        # 5. Move through 1F to the exit door (3, 8)
        # In 1F from (7, 1): move left 1 to (6, 1)
        emu.step("left", count=1)
        # Move down 6 steps along hallway x=6 to (6, 7)
        d_step = emu.step("down", count=6)
        self.assertEqual(d_step["steps_completed"], 6)
        self.assertEqual(d_step["final_position"], [6, 7])

        # Move left 3 steps to (3, 7) in front of exit mat
        l_step = emu.step("left", count=3)
        self.assertEqual(l_step["steps_completed"], 3)
        self.assertEqual(l_step["final_position"], [3, 7])

        # Step down onto exit mat -> Warps outside to Pallet Town (Map 0)!
        exit_step = emu.step("down", count=1)
        self.assertEqual(exit_step["interrupted_by"], "map_transition")

        # Verify Pallet Town arrival!
        final_state = emu.get_clean_state("scratch_pallet_town_verified.png")
        self.assertEqual(final_state["map_id"], 0)
        self.assertEqual(final_state["map_name"], "Pallet Town")
        self.assertEqual(final_state["position"], [5, 6])
        self.assertFalse(final_state["in_battle"])
        print("\n[SUCCESS] Integration test reached Pallet Town outside Player's House!")

if __name__ == "__main__":
    unittest.main()

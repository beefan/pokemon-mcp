import json
import os
from src.emulator import PokemonEmulator
from src.constants import *

PARTY_DATA_ADDR = 0xD163

class GameState:
    def __init__(self, emulator: PokemonEmulator, journal_path="game_journal.json"):
        self.emulator = emulator
        self.journal_path = journal_path
        self._ensure_journal()

    def _ensure_journal(self):
        if not os.path.exists(self.journal_path):
            initial_mission = (
                "# MISSION: The Pallet Town Arrival\n\n"
                "## Primary Objective\n"
                "Successfully navigate the intro sequence and arrive in your bedroom in Pallet Town.\n\n"
                "## Tactical Steps\n"
                "1. **Initialize**: Call `get_visual_observation`. Once 'last_observation.png' is saved, use your file reading tools to render/access it and interpret the visual content.\n"
                "2. **Start Game**: \n"
                "    - Use your vision to identify the Pokémon Title screen. Press `start` and `wait(1.0)`.\n"
                "    - Use `get_full_screen_text` or vision to verify 'NEW GAME' is visible, then press `a`.\n"
                "3. **The Oak Introduction**:\n"
                "    - Professor Oak will appear. Use `get_visual_observation` and your vision to 'see' him, and `get_dialogue_text` to read his speech.\n"
                "    - Use `advance_dialogue()` to move through his explanations.\n\n"
                "4. **CRITICAL: The Naming Screen**:\n"
                "    - If you see a grid of letters or keywords like 'ED', **DO NOT use advance_dialogue()**.\n"
                "    - Use `get_visual_observation` and access `last_observation.png` to interpret the naming grid.\n"
                "    - **To Skip Naming**: Use `press_buttons('start, wait, a')` to accept a default name.\n\n"
                "5. **Goal: The Bedroom**:\n"
                "    - You will eventually arrive in your room. Use `get_visual_observation` and `get_local_map` to verify you are in a bedroom (top-down view, Map ID 38).\n"
                "    - Once you see you are in a bedroom, use `write_journal_entry(\"MISSION COMPLETE: Arrived in Bedroom.\")` to finish.\n\n"
                "## Tactical Advice\n"
                "- **Vision Capability**: Your ability to describe image content relies on the visual rendering process (reading the file), not direct binary analysis. Always call `get_visual_observation` then read the file.\n"
                "- **Navigation**: Trust your eyes over everything else. If you see a bedroom, you are in a bedroom. Map ID 38 (0x26) is the technical verification for the starting room."
            )
            
            with open(self.journal_path, "w") as f:
                json.dump({"entries": [{"note": f"MISSION LOADED:\n{initial_mission}"}]}, f, indent=2)

    def read_journal(self):
        with open(self.journal_path, "r") as f:
            return json.load(f)

    def write_journal_entry(self, note: str):
        data = self.read_journal()
        data["entries"].append({
            "note": note
        })
        with open(self.journal_path, "w") as f:
            json.dump(data, f, indent=2)
        return "Journal updated."

    def get_party_info(self):
        """
        Reads party data from RAM.
        Returns a list of dicts.
        """
        count = self.emulator.read_ram(PARTY_DATA_ADDR)
        party = []
        
        # Address start for first mon data structure
        # After species list (count + 1 bytes?, wait Gen 1 structure is weird)
        # Gen 1 WRAM Party:
        # D163: Count
        # D164: Species 1
        # D165: Species 2
        # ...
        # D16A: Species End (0xFF)
        # D16B: Mon 1 Data Structure (44 bytes)
        # ...
        
        base_addr = 0xD16B
        mon_size = 44
        
        for i in range(count):
            addr = base_addr + (i * mon_size)
            
            # Read Values 
            # (Simplification: Just reading HP and Level for now as Species ID needs mapping)
            # Species is at offset 0
            species_id = self.emulator.read_ram(addr + 0)
            
            # Current HP at offset 1 (2 bytes, Big Endian)
            hp_high = self.emulator.read_ram(addr + 1)
            hp_low = self.emulator.read_ram(addr + 2)
            current_hp = (hp_high << 8) | hp_low
            
            # Level at offset 3? No, Box level is different.
            # Party structure:
            # 0: Species
            # 1-2: HP
            # 3: Level (Box level, inside battle it uses other RAM?)
            # Wait, d16b + 33 is Level usually.
            # Let's verify offset.
            # Offset 0x22 (34) seems to be level in some docs.
            # Let's assume Level is at offset 3 for now, need verification.
            level = self.emulator.read_ram(addr + 33) # 33 is 0x21?
            
            # Moves (4 bytes) starting at offset 8
            moves = []
            for m in range(4):
                move_id = self.emulator.read_ram(addr + 8 + m)
                if move_id != 0:
                    moves.append(move_id)
            
            party.append({
                "slot": i + 1,
                "species_id": species_id, # Needs Name Mapping
                "hp": current_hp,
                "level": level,
                "moves": moves # Needs Move Name Mapping
            })
            
        return party

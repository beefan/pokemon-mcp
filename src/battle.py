from src.emulator import PokemonEmulator
from src.constants import *
import time

class Battle:
    def __init__(self, emulator: PokemonEmulator):
        self.emulator = emulator

    def execute_action(self, action: str):
        """
        Executes a high-level battle action.
        action format: "fight_slot_1", "run", "switch_1", etc.
        """
        if action == "fight_slot_1":
            self.attack(0)
        elif action == "run":
            self.run_away()
        elif action.startswith("switch_"):
            try:
                slot = int(action.split("_")[1])
                self.switch_pokemon(slot)
            except:
                return f"Invalid switch action: {action}"
        else:
            return f"Unknown battle action: {action}"
        return "Action Executed"

    def attack(self, move_index=0):
        """
        Selects 'Fight' and then the move at move_index.
        Assumes cursor is at top-level menu.
        """
        # Menu Layout:
        # Fight  Pokemon
        # Item   Run
        
        # Cursor starts at Fight (top-left) usually? 
        # Or remembers last position? Gen 1 usually remembers last position if not careful.
        # But let's assume standard start or reset cursor.
        # Ideally, we read RAM to know cursor position.
        
        # For MVP/Macro, we might try to reset cursor implies:
        # B button a few times to get to top menu?
        
        # Sequence:
        # A (Select Fight) -> Wait -> Select Move -> A
         
        # Fight is usually top-left.
        # Press A.
        self.emulator.input(BUTTON_A)
        
        # Now in move menu.
        # Select move_index.
        # 0: Top-Left
        # 1: Top-Right? Or List? Gen 1 is a list?
        # Gen 1 Move Menu:
        # Move 1
        # Move 2
        # Move 3
        # Move 4
        
        current_index = 0
        while current_index < move_index:
            self.emulator.input(BUTTON_DOWN)
            current_index += 1
            
        self.emulator.input(BUTTON_A) # Select Move

    def run_away(self):
        """Selects 'Run'."""
        # Fight  Pokemon
        # Item   Run
        
        # Down, Right, A
        self.emulator.input(BUTTON_DOWN)
        self.emulator.input(BUTTON_RIGHT)
        self.emulator.input(BUTTON_A)

    def switch_pokemon(self, slot_index):
        """
        Open Pokemon menu and switch to slot_index (0-5).
        Note: Slot 0 is current.
        """
        # Fight  Pokemon
        # Item   Run
        
        # Right, A (Pokemon)
        self.emulator.input(BUTTON_RIGHT)
        self.emulator.input(BUTTON_A)
        
        # In Party Menu.
        # Down to slot.
        current = 0
        while current < slot_index:
            self.emulator.input(BUTTON_DOWN)
            current += 1
            
        self.emulator.input(BUTTON_A) # Select Mon
        # Menu: Switch / Stats / Cancel?
        self.emulator.input(BUTTON_A) # Select Switch (usually first option?) or need to check.
        # In Gen 1, clicking a mon brings up menu: "Shift", "Summary", "Cancel" (if battle).
        # "Shift" is top.
        self.emulator.input(BUTTON_A) # Confirm Switch

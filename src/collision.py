from src.emulator import PokemonEmulator
from src.constants import MAP_WIDTH_ADDR, COLLISION_MAP_START_ADDR, DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_ALL

# Pointer to the list of walkable tiles for the current map
W_TILESET_COLLISION_PTR = 0xD530

# Special tiles that are NOT in the standard walkable list but have specific behavior (e.g. Ledges)
# Ledges allow jumping DOWN but block UP.
# From a collision perspective:
# - Entering from North (Moving Down): Allowed (Jump).
# - Entering from South (Moving Up): Blocked.
# - Entering from Side: Blocked.
# So the mask should be DIR_DOWN (Exit South).
SPECIAL_COLLISION_OVERRIDES = {
    0x36: DIR_DOWN, # Ledge (Standard)
    0x37: DIR_DOWN, # Ledge? (Check if needed)
    0x46: DIR_DOWN, # Sandy Ledge
    0x4A: DIR_DOWN, # Sandy Ledge
}

class CollisionGrid:
    """
    Reads the true collision data from the game's memory.
    Dynamically loads the 'Walkable Tiles' list from ROM based on the current tileset.
    """
    def __init__(self, emulator: PokemonEmulator):
        self.emulator = emulator
        self.walkable_masks = {}
        self.current_map_id = -1
        self.reload_collision_data()

    def reload_collision_data(self):
        """
        Refreshes the walkable tile list from ROM.
        Should be called when the map changes.
        """
        map_id = self.emulator.get_map_id()
        # Optimization: Only reload if map changed (or strictly, if tileset changed, but map ID is a good proxy)
        if map_id == self.current_map_id and self.walkable_masks:
            return

        self.current_map_id = map_id
        self.walkable_masks = {}

        # 1. Read the pointer to the walkable list
        low = self.emulator.read_ram(W_TILESET_COLLISION_PTR)
        high = self.emulator.read_ram(W_TILESET_COLLISION_PTR + 1)
        collision_list_addr = (high << 8) | low

        # 2. Read the list until 0xFF
        # Usually implies reading from ROM (mapped in 0x0000-0x7FFF)
        if 0x0000 <= collision_list_addr <= 0x7FFF:
            curr = collision_list_addr
            limit = 256
            while limit > 0:
                val = self.emulator.read_ram(curr)
                if val == 0xFF:
                    break
                self.walkable_masks[val] = DIR_ALL
                curr += 1
                limit -= 1
        else:
            print(f"[CollisionGrid] Warning: Invalid collision list address {hex(collision_list_addr)}")

        # 3. Apply Special Overrides (Ledges, etc.)
        self.walkable_masks.update(SPECIAL_COLLISION_OVERRIDES)
        
        # 4. Apply Session-based whitelists (Bump-and-learn)
        # (Preserved if we want to keep learning across map loads? 
        # Actually, bump-and-learn should probably reset on map change or be handled carefully.
        # For now, we clear it to trust the ROM data.)

    def add_walkable_byte(self, byte: int):
        """
        Manually adds a byte to the instance's walkable whitelist.
        """
        print(f"[CollisionGrid] Manually adding walkable byte: {hex(byte)}")
        self.walkable_masks[byte] = DIR_ALL

    def mark_direction_blocked(self, byte: int, direction_mask: int):
        """
        Removes a direction from a block's bitmask if it's found to be impassable.
        """
        if byte in self.walkable_masks:
            self.walkable_masks[byte] &= ~direction_mask
            print(f"[CollisionGrid] Blocked mask {direction_mask} for byte {hex(byte)}")

    def get_map_data(self, radius=6):
        """
        Returns a detailed grid of the local area.
        Includes: Tile ID, Walkable status, Walkable Directions.
        """
        self.reload_collision_data()
        player_x, player_y = self.emulator.get_player_position()
        map_width = self.emulator.read_ram(MAP_WIDTH_ADDR)
        
        grid = []
        # Return a list of rows for easier JSON parsing
        for dy in range(-radius, radius + 1):
            row = []
            for dx in range(-radius, radius + 1):
                x = player_x + dx
                y = player_y + dy
                
                # Calculate address
                stride = map_width + 6
                offset = (y + 3) * stride + (x + 3)
                collision_addr = COLLISION_MAP_START_ADDR + offset
                collision_byte = self.emulator.read_ram(collision_addr)
                
                mask = self.walkable_masks.get(collision_byte, 0)
                
                # Determine walkable directions list
                dirs = []
                if mask & DIR_UP: dirs.append("up")
                if mask & DIR_DOWN: dirs.append("down")
                if mask & DIR_LEFT: dirs.append("left")
                if mask & DIR_RIGHT: dirs.append("right")
                
                cell = {
                    "x": x,
                    "y": y,
                    "id": hex(collision_byte),
                    "walkable": bool(mask),
                    "dirs": dirs
                }
                row.append(cell)
            grid.append(row)
                
        return {
            "map_id": self.current_map_id,
            "center": (player_x, player_y),
            "radius": radius,
            "grid": grid
        }

    def is_walkable(self, x, y, from_direction=None):
        """
        Checks if a single specific tile is walkable.
        If from_direction (bitmask) is provided, checks if movement is allowed in that direction.
        """
        self.reload_collision_data()
        map_width = self.emulator.read_ram(MAP_WIDTH_ADDR)
        stride = map_width + 6
        offset = (y + 3) * stride + (x + 3)
        collision_addr = COLLISION_MAP_START_ADDR + offset
        collision_byte = self.emulator.read_ram(collision_addr)
        
        mask = self.walkable_masks.get(collision_byte, 0)
        
        if from_direction is not None:
            return bool(mask & from_direction)
            
        return bool(mask)

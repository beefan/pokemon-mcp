from src.emulator import PokemonEmulator
from src.constants import MAP_WIDTH_ADDR, COLLISION_MAP_START_ADDR, WALKABLE_BLOCK_IDS

class CollisionGrid:
    """
    Reads the true collision data from the game's memory.
    This provides the definitive source of truth for walkability.
    """
    def __init__(self, emulator: PokemonEmulator):
        self.emulator = emulator
        # Store as a dict of BlockID -> Bitmask (Allowed Exit Directions)
        self.walkable_masks = dict(WALKABLE_BLOCK_IDS)

    def add_walkable_byte(self, byte: int):
        """
        Dynamically adds a byte to the instance's walkable whitelist.
        Useful for runtime learning (e.g., "bump" protocol).
        """
        if byte not in self.walkable_masks:
            from src.constants import DIR_ALL
            print(f"[CollisionGrid] Learned new walkable byte: {hex(byte)}")
            self.walkable_masks[byte] = DIR_ALL

    def get_collision_grid(self, radius=6):
        """
        Returns a simple boolean grid of walkable tiles around the player.
        True means walkable, False means blocked.
        This bypasses any guesswork based on visual tile IDs.
        """
        player_x, player_y = self.emulator.get_player_position()
        
        # Get the dimensions of the current map from memory.
        map_width = self.emulator.read_ram(MAP_WIDTH_ADDR)
        
        grid = {}
        for y in range(player_y - radius, player_y + radius + 1):
            for x in range(player_x - radius, player_x + radius + 1):
                # Calculate the memory address for the tile's collision data.
                stride = map_width + 6
                offset = (y + 3) * stride + (x + 3)
                collision_addr = COLLISION_MAP_START_ADDR + offset
                
                collision_byte = self.emulator.read_ram(collision_addr)
                
                # Check if it's in the whitelist (any direction allowed for simple grid)
                is_walkable = collision_byte in self.walkable_masks
                grid[f"{x},{y}"] = is_walkable
                
        return {
            "map_id": self.emulator.get_map_id(),
            "position": (player_x, player_y),
            "radius": radius,
            "collision_grid": grid
        }

    def is_walkable(self, x, y, from_direction=None):
        """
        Checks if a single specific tile is walkable.
        If from_direction (bitmask) is provided, checks if movement is allowed in that direction.
        """
        map_width = self.emulator.read_ram(MAP_WIDTH_ADDR)
        stride = map_width + 6
        offset = (y + 3) * stride + (x + 3)
        collision_addr = COLLISION_MAP_START_ADDR + offset
        collision_byte = self.emulator.read_ram(collision_addr)
        
        mask = self.walkable_masks.get(collision_byte)
        if mask is None:
            return False
            
        if from_direction is not None:
            return bool(mask & from_direction)
            
        return True

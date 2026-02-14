from src.emulator import PokemonEmulator
from src.constants import MAP_WIDTH_ADDR, COLLISION_MAP_START_ADDR, WALKABLE_BLOCK_IDS

class CollisionGrid:
    """
    Reads the true collision data from the game's memory.
    This provides the definitive source of truth for walkability.
    """
    def __init__(self, emulator: PokemonEmulator):
        self.emulator = emulator
        # Use a set for O(1) lookups. Copy from global constants to allow instance-level learning.
        self.walkable_ids = set(WALKABLE_BLOCK_IDS)

    def add_walkable_byte(self, byte: int):
        """
        Dynamically adds a byte to the instance's walkable whitelist.
        Useful for runtime learning (e.g., "bump" protocol).
        """
        if byte not in self.walkable_ids:
            print(f"[CollisionGrid] Learned new walkable byte: {hex(byte)}")
            self.walkable_ids.add(byte)

    def get_collision_grid(self, radius=6):
        """
        Returns a simple boolean grid of walkable tiles around the player.
        True means walkable, False means blocked.
        This bypasses any guesswork based on visual tile IDs.
        """
        player_x, player_y = self.emulator.get_player_position()
        
        # Get the dimensions of the current map from memory.
        # These are typically stored right before the map data itself.
        map_width = self.emulator.read_ram(MAP_WIDTH_ADDR)
        
        grid = {}
        for y in range(player_y - radius, player_y + radius + 1):
            for x in range(player_x - radius, player_x + radius + 1):
                # Calculate the memory address for the tile's collision data.
                # The map data is stored row by row with a 3-block border.
                stride = map_width + 6
                offset = (y + 3) * stride + (x + 3)
                collision_addr = COLLISION_MAP_START_ADDR + offset
                
                # Read the collision byte. In Pokémon Blue, 0x00 is often walkable,
                # and any non-zero value represents some kind of blockage.
                # This logic may need refinement based on testing.
                collision_byte = self.emulator.read_ram(collision_addr)
                
                # This is a common pattern in Gen 1 games.
                is_walkable = collision_byte in self.walkable_ids
                grid[f"{x},{y}"] = is_walkable
                
        return {
            "map_id": self.emulator.get_map_id(),
            "position": (player_x, player_y),
            "radius": radius,
            "collision_grid": grid
        }

    def is_walkable(self, x, y):
        """Checks if a single specific tile is walkable."""
        map_width = self.emulator.read_ram(MAP_WIDTH_ADDR)
        stride = map_width + 6
        offset = (y + 3) * stride + (x + 3)
        collision_addr = COLLISION_MAP_START_ADDR + offset
        collision_byte = self.emulator.read_ram(collision_addr)
        return collision_byte in self.walkable_ids

# RAM Addresses
PLAYER_X = 0xD362
PLAYER_Y = 0xD361
MAP_ID_ADDR = 0xD35E
ENEMY_HP_ADDR = 0xD057
DIALOGUE_STATE_ADDR = 0xD11B
PARTY_COUNT_ADDR = 0xD163
NAMING_SCREEN_ADDR = 0xD116 # 0 = Normal, 1 = Player, 2 = Rival
MENU_STATE_ADDR = 0xD05C    # Non-zero when a menu is open

# Hardware Registers
LCDC_ADDR = 0xFF40    # LCD Control
SCY_ADDR = 0xFF42     # Scroll Y
SCX_ADDR = 0xFF43     # Scroll X
WY_ADDR = 0xFF4A      # Window Y Position
WX_ADDR = 0xFF4B      # Window X Position

# Tile IDs (Approximate - need verification during runtime or from docs, using placeholders for now if specific IDs aren't known, 
# but common ones for Gen 1 are often documented. For now, strict collision logic might rely on the map data tool inspection)
# We will rely on get_local_map returning 'W', 'P', etc based on map scripts or raw tile ranges. 
# For now, we just export the addresses.

# Input Buttons
BUTTON_A = "a"
BUTTON_B = "b"
BUTTON_START = "start"
BUTTON_SELECT = "select"
BUTTON_UP = "up"
BUTTON_DOWN = "down"
BUTTON_LEFT = "left"
BUTTON_RIGHT = "right"

# Tile ID to Character Mapping (Pokemon Blue English)
TILE_MAP = {
    0x7F: " ", # Space
    0x01: ".", # Floor/Grass
    0x05: "#", # Wall/Solid
    0x15: "S", # Stairs
    0x3E: ">", # Door/Exit
    0xE1: "P", # PK part of PKMN
    0xE2: "M", # MN part of PKMN
    0xEE: "e", # accented e in POKEMON
    0xE0: "'",
    0x52: "<PLAYER>", # Placeholder for player name
    0x53: "<RIVAL>",  # Placeholder for rival name
    0x4A: "!",
    0x4B: ".",
    0x4E: "?",
    0x4F: ",",
    0xE6: "?",
    0xE7: "!",
    0xE8: ".",
    0xF3: "-",
    # Pallet Town / World Tiles
    0x2C: ".", # Grass/Floor (Pallet)
    0x39: "F", # Fence / Solid
    0x23: "W", # Water / Sea
    0x0B: "#", # Wall / Building
    0x08: "#", # Wall / Building
    # Oak's Lab / Interiors
    0x0F: ".", # Lab Floor
    0x10: ".", # Lab Floor
    0x11: "T", # Lab Floor/Table (observed as walkable in Oak's Lab)
    0x3B: "T", # Lab Table
    0x5B: "T", # Lab Table (Alt)
    0x58: "#", # Lab Equipment / Wall
    0x59: "#", # Lab Equipment / Wall
    0x29: "o", # Pokéball on table
    0x2A: "o", # Pokéball on table
}

# Fill A-Z (0x80 - 0x99)
for i in range(26):
    TILE_MAP[0x80 + i] = chr(65 + i)
# Fill a-z (0xA0 - 0xB9)
for i in range(26):
    TILE_MAP[0xA0 + i] = chr(97 + i)
# Fill 0-9 (0xF6 - 0xFF)
for i in range(10):
    TILE_MAP[0xF6 + i] = chr(48 + i)

# Semantic Tile Names (for describe_tile)
TILE_NAMES = {
    " ": "Floor / Open Space",
    ".": "Grass / Ground",
    "#": "Wall / Solid Object",
    "S": "Stairs (Warp)",
    ">": "Door / Exit (Warp)",
    "P": "Pokemon Symbol",
    "M": "Pokemon Symbol",
    "T": "Table / Furniture",
    "o": "Pokéball / Item",
}

GRID_LEGEND = "#:Wall, .:Floor, S:Stairs, >:Door, T:Table, o:Pokéball"

WALKABLE_CHARS = {".", " ", "S", ">"}

# Tile ID walkability overrides (used to correct misclassified tiles at runtime).
# These should be extended based on observed tile IDs from debug output.
WALKABLE_TILE_IDS = set()
NON_WALKABLE_TILE_IDS = set()

# Per-map walkability overrides. Useful when a tile ID is context-dependent.
# Map ID 40 = Oak's Lab: observed 0x11 appears walkable where the player stands.
MAP_WALKABLE_TILE_IDS = {
    40: {0x11},
}
MAP_NON_WALKABLE_TILE_IDS = {}

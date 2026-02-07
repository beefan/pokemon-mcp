# RAM Addresses
PLAYER_X = 0xD362
PLAYER_Y = 0xD361
MAP_ID_ADDR = 0xD35E
ENEMY_HP_ADDR = 0xD057
DIALOGUE_STATE_ADDR = 0xD11B
PARTY_COUNT_ADDR = 0xD163

MAP_NAMES = {
    0: "Pallet Town",
    1: "Red's House 1F",
    2: "Red's House 2F (Bedroom)",
    3: "Rival's House",
    4: "Oak's Lab",
    5: "Viridian City",
    6: "Viridian City Gym",
    # We can add more as needed
}

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


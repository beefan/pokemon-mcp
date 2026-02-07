# RAM Addresses
PLAYER_X = 0xD362
PLAYER_Y = 0xD361
MAP_ID_ADDR = 0xD35E
ENEMY_HP_ADDR = 0xD057
DIALOGUE_STATE_ADDR = 0xD11B
PARTY_COUNT_ADDR = 0xD163

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

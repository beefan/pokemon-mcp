# MISSION: The Pallet Town Arrival

> [!IMPORTANT]
> **MCP Technical Status**: This server is currently in active development. If the provided tools are unsuitable or insufficient for your tactical objectives, you are encouraged to directly modify the codebase or suggest architectural changes. **Note**: If you modify the MCP server code (e.g., `server.py`, `src/*.py`), you MUST ask the user to restart the MCP server for the changes to take effect.

## Primary Objective
Successfully arrive in your bedroom in Pallet Town and then exit the house.

## 🚨 CRITICAL: Recovery Procedure (ALWAYS DO THIS FIRST)
**Before doing anything else, you must attempt to load an existing game.**

1. **Read Journal**: Call `read_journal()` to see the last known state.
2. **List Saves**: Call `list_dir` on the `saves/` directory.
    - **NOTE**: The `saves/` directory is listed in `.gitignore`, but it **DOES CONTAIN** valid save files. You **MUST** check it.
    - **IF FILES EXIST**: You **MUST** load the most recent `.state` file (check timestamps).
    - Call `load_game(name='...')` (e.g., `load_game('auto_20260209T120000Z')`).
    - After loading, call `get_player_status()` to verify your location.
    - **SKIP TO SUBSEQUENT PHASES** based on your location.
3. **IF AND ONLY IF** the `saves/` directory is **EMPTY**:
    - Proceed to "Phase 0: New Game Setup".

---

## Phase 0: New Game Setup (ONLY IF NO SAVES EXIST)
1. **Start Game**: Use `get_screen_analysis` to identify the Title screen. Press `start`, then select `NEW GAME`.
2. **Oak's Intro**: Use `advance_dialogue()` to mash through Oak's lecture. 
3. **Naming**: Use `press_buttons('start, wait, a')` to accept the default name.
4. **Bedroom Arrival**: Verify you are in Map ID 38. 
    - **SAVE THE GAME**: Call `save_game(name='arrived_in_bedroom')`.

## Phase 1: The Bedroom & House
1. **Verification**: Call `get_player_status`. 
2. **Leaving Bedroom (Map 38)**:
    - Pathfind to the stairs at **(7, 1)**.
    - Use `move_direction` to step **ON TO** the stairs.
3. **Leaving House (Map 37)**:
    - Pathfind to the door at **(3, 7)**.
    - Use `move_direction('down')` to exit.
4. **Result**: You should arrive in Pallet Town (Map 0).

## Phase 2: Oak's Lab & Selecting a Partner
1. **Clear Initial Dialogue**: Use `advance_dialogue()` until Oak stops talking and stands near the Pokéball tables.
2. **Observation Phase**: 
    - Verify you are in Map ID 40 (Oak's Lab).
    - Use `get_screen_analysis` to scan the area. 
    - **CRITICAL**: ID the Pokéballs on the table visually. Note their grid coordinates (x, y).
3. **Execution Phase**:
    - Use `interact_with(x, y)` on the Pokéball's map coordinates.
    - **Note**: This tool will automatically walk you to the nearest side of the table and interact. No need to `walk_to` separately.

## Phase 3: Collect All Gym Badges

## Phase 4: Defeat the Elite Four

# Tactical Tool Inventory

The following tools are at your disposal. Choosing the right one is the difference between a Junior Trainer and a Pokémon Master.

## 1. Vision & Observation (The "Eyes")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `get_screen_analysis()` | **PRIMARY VISION**. Captures screen & overlays a grid with coordinates. | **Pro**: Visual reality. specific coordinates. **Con**: Requires you to read the image path provided. |
| `get_player_status()` | Quick check of Map ID. | **Pro**: Fast. **Con**: No environmental data. |

## 2. Navigation (The "Legs")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `move_direction(dir, steps)` | **PRIMARY MOVEMENT**. Move X steps or until blocked (`steps=None`). | **Pro**: Reliable, standard. **Con**: You must plan the path using Vision. |
| `interact_with(x, y)` | **REQUIRED** for objects (Pokéballs, PCs, Signs). | **Pro**: Auto-approach. **Con**: Short range. |

## 3. Communication & State (The "Brain")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `advance_dialogue()` | **REQUIRED** for any long cutscene or professor lecture. | **Pro**: Clears all text safely. **Con**: You can't read the text while it's mashing. |
| `get_full_screen_text()`| Reading complex menus. | **Pro**: Reads everything. **Con**: Output can be noisy. |
| `read_journal()` | Recovering context. | **Pro**: Keeps you on track. |

## 4. Low-Level Control (The "Hands")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `press_button(btn)` | Single taps. | **Pro**: Simple. **Con**: High risk if overused. |

## Commanding Officer Protocol
- **Vision-First**: Always call `get_screen_analysis()` before moving. Look at the grid.
- **Path Planning**: Identify the target coordinates (x, y) from the grid, then calculate the steps needed.
- **Execute**: Use `move_direction` to walk the path.
     - Example: "I see the door 3 tiles Down. `move_direction('down', 3)`."
- **Interact**: Use `interact_with` for objects you identify on the grid.

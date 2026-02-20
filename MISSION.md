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
    - Use `walk_to(7, 1)` to automatically navigate to the stairs.
    - Use `move_direction` to step **ON TO** the stairs if `walk_to` stops adjacent.
3. **Leaving House (Map 37)**:
    - Use `get_local_map()` to find the door coordinates (usually near the bottom).
    - Use `walk_to(x, y)` to reach the exit mat.
4. **Result**: You should arrive in Pallet Town (Map 0).

## Phase 2: Oak's Lab & Selecting a Partner
1. **Clear Initial Dialogue**: Use `advance_dialogue()` until Oak stops talking and stands near the Pokéball tables.
2. **Observation Phase**: 
    - Verify you are in Map ID 40 (Oak's Lab).
    - Use `get_local_map()` to identify the walkable path to the table.
    - Use `get_screen_analysis()` to visualy ID the Pokéballs. Note their grid coordinates (x, y).
3. **Execution Phase**:
    - Use `interact_with(x, y)` on the Pokéball's map coordinates.
    - **Note**: This tool will automatically walk you to the nearest side of the table and interact.

## Phase 3: Route 1 & Viridian City
1. **Traverse Route 1**: 
    - Use `get_local_map(radius=10)` to scan a large area ahead.
    - Identify open paths through the ledges. **Note**: Ledges are one-way (jump down). You cannot walk up them.
    - Use `walk_to(x, y, on_battle='run')` to move through the route efficiently.
2. **Handle POIs**: If you encounter an NPC, use `get_screen_analysis()` to identify them.

# Tactical Tool Inventory

The following tools are at your disposal. Choosing the right one is the difference between a Junior Trainer and a Pokémon Master.

## 0. Navigation Memory & The Journal (The "Memory")
The MCP server automatically logs all navigation attempts to the Game Journal. 

| Tool | Usage for Navigation |
| :--- | :--- |
| `read_journal()` | **CRITICAL**. Call this if you get stuck or restart. Look for `NavLog` entries. |
| `write_journal_entry()`| Use this to log strategic notes (e.g., "Found a path around the ledge at (10,13)"). |

### How to use NavLogs:
- **`BLOCKED at (x, y)`**: If you see this in the journal, do not try to walk to or through that coordinate again in the same map.
- **`map_transition`**: You have successfully moved to a new area.

## 1. Vision & Observation (The "Eyes")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `get_local_map(radius)` | **PRIMARY MAPPING**. Scans the ROM for true collision data. | **Pro**: Shows exactly where you can walk. IDs Ledges. **Con**: No visual sprites. |
| `get_screen_analysis()` | **VISUAL CONFIRMATION**. Captures screen & overlays a grid. | **Pro**: Visual reality. specific coordinates. **Con**: High token cost to read. |
| `get_player_status()` | Quick check of Map ID and coordinates. | **Pro**: Fast. **Con**: No environmental data. |

## 2. Navigation (The "Legs")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `walk_to(x, y)` | **LONG-RANGE AUTO-PILOT**. Navigate to map coordinates. | **Pro**: Uses Deep Map A* pathfinding. Avoids ledges. **Con**: Stops on battle. |
| `move_direction(dir, steps)` | **PRECISION MOVEMENT**. Move X steps. | **Pro**: High-fidelity verification (X, Y, Visual Hash). **Con**: Manual pathing. |
| `interact_with(x, y)` | **REQUIRED** for objects (Pokéballs, PCs, Signs, talking to people). | **Pro**: Auto-approach and face. **Con**: Short range. |

## 3. Communication & State (The "Brain")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `advance_dialogue()` | **REQUIRED** for any long cutscene or professor lecture. | **Pro**: Clears all text safely. **Con**: You can't read the text while it's mashing. |
| `read_journal()` | Recovering context. | **Pro**: Keeps you on track. |

## 4. Low-Level Control (The "Hands")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `press_button(btn)` | Single taps. | **Pro**: Simple. **Con**: High risk if overused. |

## Commanding Officer Protocol
- **Survey-First**: Always call `get_local_map()` first to understand the terrain (walls, ledges).
- **Plan**: Choose a target coordinate (x, y) that is reachable.
- **Execute**: Use `walk_to(x, y)` to travel there.
- **Interact**: Use `interact_with` for objects you identify.

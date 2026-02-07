# MISSION: The Pallet Town Arrival

## Primary Objective
Successfully arrive in your bedroom in Pallet Town and then exit the house.

## Phase 0: Setup & Branching
1. **Check for Saves**: 
    - Use `list_dir` on the `saves/` directory. 
    - If `arrived_in_bedroom.state` exists, call `load_state` and **SKIP DIRECTLY TO PHASE 2**.
2. **Continue to Phase 1** only if no save exists.

## Phase 1: The Intro & Arrival
1. **Start Game**: Use vision/text to identify the Title screen. Press `start`, then select `NEW GAME`.
2. **Oak's Intro**: Use `advance_dialogue()` to mash through Oak's lecture. 
3. **Naming**: Use `press_buttons('start, wait, a')` to accept the default name.
4. **Bedroom Arrival**: Verify you are in Map ID 38. 
    - **SAVE THE GAME**: Call `save_game(name='arrived_in_bedroom')`.

## Phase 2: Leaving the House
1. **Verification**: Call `get_player_status`. 
    - If Map ID is 38 (Bedroom): Pathfind to the stairs at **(7, 1)**.
    - If Map ID is 37 (Downstairs): Pathfind to the door at **(3, 7)**.
2. **Exiting**: 
    - Use `move_direction` to step **ON TO** stairs or **THROUGH** doors. 
    - **NOTE**: House exits (Map 37 -> Map 0) use the `move_direction('down')` at `(3, 7)`. 
    - If `move_direction` returns "success", you have transitioned.

## Phase 3: Oak's Lab & Selecting a Partner
1. **Clear Initial Dialogue**: Use `advance_dialogue()` until Oak stops talking and stands near the Pokéball tables.
2. **Observation Phase**: 
    - Verify you are in Map ID 40 (Oak's Lab).
    - Use `get_local_map` to scan the area. 
    - **CRITICAL**: Check the `nearby_objects` list in the JSON return. It will explicitly list the map coordinates of all Pokéballs ('o').
3. **Execution Phase**:
    - Use `interact_with(x, y)` on the Pokéball's map coordinates found in the previous step.
    - **Note**: This tool will automatically walk you to the nearest side of the table and interact. No need to `walk_to` separately.

# Tactical Tool Inventory

The following tools are at your disposal. Choosing the right one is the difference between a Junior Trainer and a Pokémon Master.

## 1. Navigation (The "Legs")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `walk_to(x, y)` | Long distance travel to known coords. | **Pro**: Smart pathfinding, warp avoidance. **Con**: Can get stuck in very tight corners (use `interact_with` for objects). |
| `move_direction(dir, steps)` | Precise 1-tile shifts, entering doors, or "mashing" until blocked. | **Pro**: Most reliable for transitions. **Con**: "Dumb" - doesn't avoid obstacles or realize it's stuck. |
| `interact_with(x, y)` | **REQUIRED** for objects on tables (Pokéballs), PCs, or stationary people. | **Pro**: Handles approach/facing/A-press automatically. **Con**: Only works on neighboring tiles. |

## 2. Observation (The "Eyes")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `get_local_map()` | **PRIMARY VISION**. Scan the area for objects and layout. | **Pro**: Lists `nearby_objects` (Pokéballs) with coordinates. **Con**: Text-based; doesn't show NPC sprites clearly. |
| `get_player_status()` | Quick check of Map ID and proximity to warps. | **Pro**: Fastest way to verify location. **Con**: No layout data. |
| `get_visual_observation()`| When menus, titles, or battle screens are active. | **Pro**: Actual visual of the game. **Con**: Requires manual file reading and takes time. |
| `describe_tile(x, y)` | Identifying a specific mystery tile ID. | **Pro**: Semantic info (e.g., "Wall"). **Con**: Single-tile only. |

## 3. Communication & State (The "Brain")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `advance_dialogue()` | **REQUIRED** for any long cutscene or professor lecture. | **Pro**: Clears all text safely. **Con**: You can't read the text while it's mashing (use `get_dialogue_text` first if needed). |
| `get_full_screen_text()`| Reading complex menus (Bag, PC, Options). | **Pro**: Reads everything. **Con**: Output can be noisy. |
| `read_journal()` | Recovering context after a reload or disconnect. | **Pro**: Keeps you on track. **Con**: Only as good as the notes you write. |

## 4. Low-Level Control (The "Hands")

| Tool | When to Use | Trade-offs |
| :--- | :--- | :--- |
| `press_button(btn)` | Single taps for confirming choices or opening menus. | **Pro**: Simple. **Con**: High risk of losing state if overused. |
| `press_buttons(seq)` | Macros like 'start,wait,a' to save or check stats. | **Pro**: Fast. **Con**: Fragile; timings might fail. |

## Commanding Officer Protocol
- **Observe Before Acting**: If you enter a new room or a long scene ends, ALWAYS call `get_player_status` or `get_local_map`. 
- **Tool Priority**: 
    - Use `advance_dialogue()` for all text Cutscenes. 
    - Use `interact_with(x, y)` for any object you cannot step on (Pokéballs, PCs, Signs).
    - Use `walk_to` for distance. 
    - Use `move_direction` ONLY for precise 1-tile steps.
- **Self-Sufficiency**: Do not guess coordinates. The `get_local_map` tool provides a labeled grid and an object list—use them!

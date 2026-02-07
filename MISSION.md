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
    - Use `get_local_map` to scan the tables. 
    - Identify the coordinates of the Pokéballs (look for specific tile characters or use `describe_tile`).
3. **Execution Phase**:
    - Use `walk_to(x, y)` to reach the table with your desired Pokémon.
    - Interact with the ball and confirm with `press_button('a')`.

## Commanding Officer Protocol
- **Observe Before Acting**: If you enter a new room or a long scene ends, ALWAYS call `get_player_status` or `get_local_map`. 
- **Tool Priority**: 
    - Use `advance_dialogue()` for all text. 
    - Use `walk_to` for distance. 
    - Use `move_direction` ONLY for precise 1-tile steps.
- **Self-Sufficiency**: Do not guess coordinates. The `get_local_map` tool provides a labeled grid—use it to find your targets.

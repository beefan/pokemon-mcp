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

## Tactical Advice
- **AUTONOMY**: Use `get_player_status` or `get_local_map` to determine your position.
- **Vision**: Use your file tools to read `last_observation.png`.
- **Navigation**: 
    - Use `walk_to` for distance.
    - Use `move_direction` for precise steps onto warps (stairs/doors).
    - If blocked by tile `0x7F`, it is likely an invisible wall or an exit mat that requires a specific direction.

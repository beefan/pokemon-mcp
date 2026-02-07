# MISSION: The Pallet Town Arrival

## Primary Objective
Successfully navigate the intro sequence and arrive in your bedroom in Pallet Town.

## Tactical Steps
0. **Check for Saves**: 
    - Use `list_dir` on the `saves/` directory. 
    - If a recent save exists (e.g., `arrived_in_bedroom.state`), call `load_state(filepath='saves/arrived_in_bedroom.state')`.
1. **Initialize**: Call `get_visual_observation` and view 'last_observation.png' using your file tools to confirm your surroundings.
2. **Start Game**: 
    - Use vision to identify the Pokémon Title screen. Press `start` and `wait(1.0)`.
    - Verify 'NEW GAME' is visible via `get_full_screen_text`, then press `a`.
3. **The Oak Introduction**:
    - Advance through Oak's dialogue using `advance_dialogue()`.
    - **CRITICAL**: If `advance_dialogue` returns a **STOP** or **LOOP** error, follow its instructions immediately.
4. **The Naming Screen**:
    - When you reach the naming grid, `advance_dialogue` will block you.
    - **Action**: Use `press_buttons('start, wait, a')` to accept the default name. If you are still there, use `press_button('a')` once.
5. **Arrival at Bedroom (Map ID 38)**: 
    - Verify your location by calling `get_visual_observation` and confirming you see the TV, SNES, or Bed.
    - **SAVE THE GAME**: Call `save_game(name='arrived_in_bedroom')` immediately upon visual confirmation.
6. **Phase 2: Leave the House**:
    - Walk to the stairs at **(7, 1)**. If `walk_to` says "stopped: dialogue active", clear the screen first!
    - Downstairs (1F), walk south to the door at **(3, 7)** to exit.

## Tactical Advice
- **AUTONOMY**: You are the Commanding Officer. You have all the tools. DO NOT ask the human to "tell you what's on the screen." Call `get_player_status` or `get_local_map` to determine your position.
- **Vision**: Reminder: You CAN use your file tools to read and describe images. don't be shy about using it!
- **Navigation**: 
    - Use `walk_to` for long-distance travel.
    - If `walk_to` returns "no path found," call `get_player_status`. 
    - Use `move_direction` for precise, single-tile steps (especially to step ON TO stairs or doors). 
    - If blocked, `move_direction` will report the specific tile ID causing the obstruction.

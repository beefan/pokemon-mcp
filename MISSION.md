# MISSION: The Pallet Town Arrival

## Primary Objective
Successfully navigate the intro sequence and arrive in your bedroom in Pallet Town.

## Tactical Steps
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
- **AUTONOMY**: You are the Commanding Officer. You have all the tools. DO NOT ask the human to "tell you what's on the screen." Call `get_visual_observation` and read the file yourself.
- **Navigation**: You must walk **ON TO** exit tiles (stairs/doors). If `walk_to` stops, check why (Dialogue? Wall?).

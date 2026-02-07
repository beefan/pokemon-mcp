# MISSION: The Pallet Town Arrival

## Primary Objective
Successfully navigate the intro sequence and arrive in your bedroom in Pallet Town.

## Tactical Steps
1. **Initialize**: Call `get_visual_observation`. Once 'last_observation.png' is saved, use your file reading tools to render/access it and interpret the visual content.
2. **Start Game**: 
    - Use your vision to identify the Pokémon Title screen. Press `start` and `wait(1.0)`.
    - Use `get_full_screen_text` or vision to verify 'NEW GAME' is visible, then press `a`.
3. **The Oak Introduction**:
    - Professor Oak will appear. Use `get_visual_observation` and your vision to 'see' him, and `get_dialogue_text` to read his speech.
    - Use `advance_dialogue()` to move through his explanations.

4. **CRITICAL: The Naming Screen**:
    - If you see a grid of letters or keywords like 'ED', **DO NOT use advance_dialogue()**.
    - Use `get_visual_observation` and access `last_observation.png` to interpret the naming grid.
    - **To Skip Naming**: Use `press_buttons('start, wait, a')` to accept a default name.

5. **Goal: The Bedroom**:
    - You will eventually arrive in your room (Map ID 38).
    - Use `get_visual_observation` to confirm you are in the bedroom.
    - **SAVE THE GAME**: Call `save_game(name='arrived_in_bedroom')` immediately.

6. **Phase 2: Leave the House**:
    - Walk to the stairs at **(7, 1)** to go down to 1F.
    - On 1F, walk south to the door at **(3, 7) or (2, 7)** to exit to Pallet Town.
    - Once outside (Map ID 0), walk south to the large building (Oak's Lab).

## Tactical Advice
- **Navigation**: To exit a room, you must walk **ON TO** the exit tile (stairs or door).
- **Stuck?**: If `walk_to` returns `blocked`, use `get_visual_observation` to see what is in your way (NPCs or walls).
- **Vision Capability**: Your ability to describe image content relies on the visual rendering process (reading the file), not direct binary analysis. Always call `get_visual_observation` then read the file.
- **Dialogue Loops**: If `advance_dialogue` says **STATE CHANGE: Dialogue has CLOSED**, you must **STOP** mashing and use `walk_to`. If you keep mashing while facing an object (like the SNES), you will trigger the SAME dialogue repeatedly.
- **Limits**: `walk_to` is limited to 50 steps. If you aren't there yet, call it again.

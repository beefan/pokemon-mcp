# PROPOSAL: Project "Viridian" - Robust Agentic Pokemon Interfacing

## Executive Summary
The current MCP server ("og-pokemon-mcp") suffers from a "Desynchronization of Reality". The Agent's visual perception (via screenshots) contradicts its physical constraints (via incorrect RAM interpretation). This leads to the agent "hallucinating" paths that are physically blocked, or believing it is trapped when it is free.

This proposal outlines **Project Viridian**: a refactoring initiative to bridge the gap between Vision and RAM, creating a `Hybrid Commanding Officer` that trusts its eyes but validates with its hands.

---

## 1. The Core Issues

### A. The "Glass Wall" Problem (Collision Disconnect)
*   **Observation**: `src/collision.py` assumes only bytes `0x00` and `0x11` are walkable.
*   **Reality**: Pokemon Blue uses complex tile sets. Grass, door mats, distinctive floors, and changing event tiles often have different IDs (e.g. `0x0C`, `0x2C`).
*   **Consequence**: The A* pathfinder (`walk_to`) refuses to route through valid terrain, returning local "blocked" errors, while the Agent sees an open field.

### B. The "Blind Walker" Problem (Navigation Feedback)
*   **Observation**: `move_direction` returns generic "blocked" messages.
*   **Reality**: It doesn't tell the agent *what* blocked it (a wall? an NPC? an invisible script tile?).
*   **Consequence**: The agent loops, trying to push through a wall it thinks shouldn't be there.

### C. The "Silent World" Problem (Interaction Feedback)
*   **Observation**: `interact_with` presses 'A' but gives little semantic feedback.
*   **Reality**: The agent doesn't know if the interaction triggered a text box, a map transition, or nothing.
*   **Consequence**: The agent mashes 'A' on a door, expects to leave, but stays in the room because the door is actually a "Step-On" warp, not an "Interact" warp.

---

## 2. Proposed Architecture: The "Hybrid Pathfinder"

We will move from a "RAM-Only" pathfinder to a **Hybrid Vision/RAM** system.

### Component A: `Collision Oracle` (Refactored `src/collision.py`)
Instead of a hardcoded whitelist, we implement a **Dynamic Collision Map**.
1.  **Heuristic Expansion**: Add more known walkable tiles (Grass, Sand, Lab Floor) to the whitelist immediately.
2.  **Runtime Calibration**: A new tool `scan_local_collision()` that returns the raw collision bytes for the 5x5 grid around the player.
3.  **The "Bump" Protocol**: If the Agent attempts to walk onto a tile marked "Blocked" by RAM but "Open" by Vision, it can *override* the pathfinder to attempt a single step. If successful, that tile ID is added to a `session_walkable_cache`.

### Component B: `Vision-Navigation Link`
New Tool: `visual_guided_step(direction, expected_visual_change)`
*   The Agent provides a direction and a description (e.g., "I expect to see the door get closer").
*   The tool calculates the move, executes it, and *verifies* with a perceptual check (did coordinates change? did the screen shift?).

### Component C: `Event State Manager`
New Tool: `get_game_state_flags()`
*   We will expose key Event Flags (RAM) to track progress.
*   Examples: "Starter Chosen?", "Oak's Parcel Delivered?", "Rival Defeated?".
*   This removes the guesswork of "Did I trigger the event?".

---

## 3. Implementation Plan (Broad Strokes)

1.  **Phase 1: Knowledge Acquisition (Immediate)**
    *   Create `inspect_tile_memory(x, y)`: A debug tool to read the specific byte at `0xC4A0 + offset` for any coordinate.
    *   **Agent Task**: Agent walks around Pallet Town/Lab, logging the memory values of floor, grass, wall, door.
    *   **Outcome**: A verified `WALKABLE_TILE_IDS` set for `constants.py`.

2.  **Phase 2: Navigation Refactor**
    *   Update `src/navigation.py` to use the new `WALKABLE_TILE_IDS`.
    *   Implementing a "Stuck? Try Random Neighbor" heuristic in `walk_to`.
    *   Fix `interact_with` to differentiate between "Face & Interact" vs "Step On" (for Warps).

3.  **Phase 3: Event Awareness**
    *   Research RAM map for "Event Flags" (Address `0xD700` series usually).
    *   Implement `get_story_progress()` to report integer flags.

---

## 4. Immediate Next Steps

I will generate a `TICKETS.md` file breaking these phases down into small, code-focused tasks (e.g., "Update `constants.py` with expanded tile list", "Refactor `Navigation.find_path`").

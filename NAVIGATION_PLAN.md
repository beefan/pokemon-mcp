# Navigation Tool Polish: Step & Scout Strategy

This plan outlines improvements to the movement tools in the Pokémon Blue MCP, specializing them for situational awareness and stable long-range traversal.

## Core Objectives

1.  **High-Fidelity Stepping**: Consolidate `move_direction` and `visual_guided_step` into a single tool that provides rich sensory feedback (Coordinates, Visual Hash, Tile Type, Collision Byte).
2.  **Safe Scouting**: Implement a "Scout" tool that moves until it hits a point of interest (NPC, Warp, Transition, or Blockage), reducing LLM overhead.
3.  **Situational Awareness**: Ensure the agent understands *why* movement stopped without needing separate inspection calls.

## Proposed Tools

### 1. Enhanced `move_direction` (The "Step" Tool)
Refine the existing `move_direction` to use the logic from `visual_guided_step` for better verification.

- **Inputs**: `direction`, `steps=1`.
- **Logic**:
    - Record initial state (Map ID, X, Y, Screen Hash).
    - Send input.
    - Wait and record post-state.
- **Feedback**:
    - `success`: Result of coordinate change.
    - `visual_change`: True if screen hash changed but coordinates didn't (Treadmills, bumps).
    - `tile_info`: The `{char, tid, collision_byte}` of the target tile.
    - `event`: "NPC approaching", "Battle started", or "Map transition".

### 2. `scout_ahead` (The "Scout" Tool)
A higher-level traversal tool for clearing routes and hallways.

- **Inputs**: `direction`, `max_steps=10`.
- **Logic**:
    - Loops the "Step" logic until a **Stop Condition** is met.
- **Stop Conditions**:
    1.  **Map transition**: Map ID changed.
    2.  **Battle started**: RAM address `0xD057` > 0.
    3.  **Blocked**: Coordinate change = 0 and `visual_change` = False.
    4.  **Point of Interest**:
        - Adjacent to an **NPC**.
        - Current tile or next tile is a **Warp** (`S` or `>`).
- **Return**: A summary of steps taken and the exact reason for stopping.

## Dependency Note
Implementing these tools provides the infrastructure needed for **PKM-8 (Bump-and-Learn)**. Once the "Step" tool can reliably detect and report collision bytes on failure, we can easily cache those failures as dynamic blockages in the `CollisionGrid`.

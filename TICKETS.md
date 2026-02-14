# Jira Tickets

| Key | Summary | Status | Goal |
|---|---|---|---|
| **PKM-1** | [OPS-001] Create debug_inspect_tile Tool | Done | Debug tool for inspecting tiles. |
| **PKM-2** | [OPS-002] Create CollisionSurveyor Script | Done | Map Pallet Town's collision data. |
| **PKM-3** | [CORE-001] Refactor CollisionGrid for Dynamic Whitelists | To Do | Stop assuming 0x00 is the only walkable tile. |
| **PKM-4** | [NAV-001] Implement visual_guided_step | Done | Tool that moves blindly but verifies visually. |
| **PKM-5** | [NAV-002] Oscillation Breaker in walk_to | Done | Prevent infinite left-right loops. |
| **PKM-6** | [NAV-003] Enrich move_direction Feedback | To Do | Tell the agent *why* it was blocked. |
| **PKM-7** | [NAV-004] Fix interact_with Feedback | To Do | Distinguish "Face & Press A" from "Step-On" warps. |
| **PKM-8** | [CORE-002] Bump-and-Learn Session Cache | To Do | Runtime collision learning. |
| **PKM-9** | [STATE-001] Implement get_game_state_flags | To Do | Read story progress from RAM. |
| **PKM-10** | [UX-001] Advanced Dialogue Handling | To Do | Handle Yes/No prompts better. |
| **PKM-11** | [TECH-001] Tech Debt & Stability | To Do | Code cleanup and stability fixes. |
| **PKM-12** | [NAV-005] Pathfinder Directional Constraints | To Do | Handle one-way tiles like ledges. |

## Detailed Descriptions

### PKM-3: [CORE-001] Refactor CollisionGrid
- **Goal**: Stop assuming `0x00` is the only walkable tile.
- **Implementation**: Import `WALKABLE_TILE_IDS` from constants. Update `is_walkable` to check whitelist. Add `add_walkable_byte`.

### PKM-4: [NAV-001] Implement visual_guided_step
- **Goal**: A tool that moves blindly but verifies visually.
- **Usage**: "I think this wall is fake. Move UP and check if my Y coordinate changed."

### PKM-5: [NAV-002] Oscillation Breaker
- **Goal**: Prevent infinite left-right loops in `walk_to`.
- **Implementation**: Track history and force random steps if looping.

### PKM-6: [NAV-003] Enrich move_direction Feedback
- **Goal**: Tell the agent *why* it was blocked (NPC, Script Tile, Wall).

### PKM-7: [NAV-004] Fix interact_with Feedback
- **Goal**: Distinguish "Press A" from "Step-On" warps.

### PKM-8: [CORE-002] Bump-and-Learn Session Cache
- **Goal**: Runtime collision learning. cache walkable tiles on successful "bumps".

### PKM-9: [STATE-001] Implement get_game_state_flags
- **Goal**: Read story progress (Oak Parcel, Rival) from RAM.

### PKM-10: [UX-001] Advanced Dialogue Handling
- **Goal**: Detect Yes/No prompts and return "Prompt Active".

### PKM-11: [TECH-001] Tech Debt & Stability
- **Goal**: General code cleanup, refactoring, and stability improvements.

### PKM-12: [NAV-005] Pathfinder Directional Constraints
- **Goal**: Handle one-way tiles like ledges and treadmills in the pathfinder.
- **Implementation**: Update `is_walkable` to accept a `from_direction` and check directional bitmasks.

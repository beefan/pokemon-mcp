# Project Viridian: Engineering Tickets

This document outlines the specific engineering tasks required to implement the "Hybrid Commanding Officer" architecture.

---

## 🛠️ Operations & Tooling (OPS)

### [OPS-001] Create `scan_memory_region` Tool
**Goal**: Allow the Agent to inspect raw memory around a coordinate to "learn" the true collision bytes.
*   **File**: `src/emulator.py`, `server.py`
*   **Implementation**:
    *   Add `read_map_memory(x, y)` to `emulator.py`.
    *   It should calculate the RAM address `0xC4A0 + (y * width) + x`.
    *   Expose as MCP tool `debug_inspect_tile(x, y)`.
*   **Acceptance Criteria**: Agent can stand on a rug and report "Tile at (5,5) has collision byte 0x0C".

### [OPS-002] Create `CollisionSurveyor` Script
**Goal**: A specialized script (or Agent prompt) to map Pallet Town.
*   **Context**: We need to know the byte values for: Grass, Signposts, Doors, Carpets, Tables.
*   **Deliverable**: A JSON file or Update to `constants.py` with `WALKABLE_BYTE_Set = {0x00, 0x01, 0x0C, ...}`.

---

## 🧠 Core Logic (CORE)

### [CORE-001] Refactor `CollisionGrid` for Dynamic Whitelists
**Goal**: Stop assuming `0x00` is the only walkable tile.
*   **File**: `src/collision.py`
*   **Implementation**:
    *   Import `WALKABLE_TILE_IDS` from `constants.py`.
    *   Update `is_walkable(x, y)` to check constraints: `byte in WALKABLE_TILE_IDS`.
    *   Add a method `add_walkable_byte(byte)` to allow runtime learning.
*   **Acceptance Criteria**: `get_local_grid` reports "Walkable" for tiles previously marked "Blocked" if they are in the new whitelist.

---

## 🚶 Navigation (NAV)

### [NAV-001] Implement `visual_guided_step`
**Goal**: A tool that moves blindly but verifies visually.
*   **File**: `src/navigation.py`
*   **Usage**: "I think this wall is fake. Move UP and check if my Y coordinate changed."
*   **Implementation**:
    *   Takes `direction`.
    *   Diffs `emulator.screen_image()` before and after (or just pixel sum/hash).
    *   Diffs `player_position`.
    *   Returns: "Moved successfully", "Blocked (No visual change)", or "Visual change but position same" (treadmill?).
*   **Acceptance Criteria**: Agent can use this to enter the Lab "Door" even if collision map says it's a wall.

### [NAV-002] Oscillation Breaker in `walk_to`
**Goal**: Prevent infinite left-right loops.
*   **File**: `src/navigation.py`
*   **Implementation**:
    *   Track `history_positions = deque(maxlen=4)`.
    *   If `history` shows `A -> B -> A -> B` pattern:
        *   Force a "Random Step" to a valid neighbor C (that isn't B).
        *   Log "Oscillation broken via random step to {C}".
*   **Acceptance Criteria**: Agent gets un-stuck from corners automatically.

### [NAV-003] Enrich `move_direction` Feedback
**Goal**: Tell the agent *why* it was blocked, not just *that* it was blocked.
*   **File**: `src/emulator.py` -> `move_direction`
*   **Problem**: Currently returns generic `"blocked by W"` or `"blocked by <PLAYER>"` strings derived from `TILE_MAP` lookups. NPC sprites, script tiles, and invisible walls all produce confusing labels.
*   **Implementation**:
    *   After a failed move, read the collision byte at the target tile and include it: `"blocked: collision_byte=0x3E (Door tile)"`.
    *   Detect NPC sprites via OAM/sprite data or known NPC RAM addresses and report `"blocked by NPC"` explicitly.
    *   Detect dialogue/script triggers and report `"blocked: script tile (event trigger?)"`.
*   **Acceptance Criteria**: Agent receives actionable info like `"blocked by NPC at (5,3)"` or `"blocked: warp tile, try stepping ON it"` instead of `"blocked by >"`.

### [NAV-004] Fix `interact_with` Feedback & Warp Differentiation
**Goal**: Make `interact_with` return *what happened*, and distinguish "Face & Press A" interactions from "Step-On" warps.
*   **File**: `src/navigation.py` -> `interact_with`
*   **Problem**: Returns `"interaction_success"` with no indication of the result. Doors in Gen 1 are often "Step-On" warps (you walk onto them), not "Press A" interactions. The agent presses A on a door mat and nothing happens.
*   **Implementation**:
    *   After pressing A, check for state changes: did dialogue appear? did map ID change? did position change?
    *   Return rich feedback: `"interaction_success: dialogue_started"`, `"interaction_success: map_changed to 40"`, or `"interaction_failed: no state change detected"`.
    *   Add warp-type hints: if the target tile char is `">"` or `"S"`, suggest `"This is a step-on warp. Use move_direction to walk onto it instead of interact_with."`.
*   **Acceptance Criteria**: Agent knows when to walk onto a door vs press A on it, and gets clear post-interaction feedback.

---

## 🧠 Core Logic (CORE) — continued

### [CORE-002] "Bump-and-Learn" Session Cache
**Goal**: Allow runtime collision learning so the agent can teach itself what tiles are walkable.
*   **File**: `src/collision.py`
*   **Context**: Proposal Component A.3 — "The Bump Protocol". If the Agent successfully walks onto a tile that the collision whitelist says is blocked, that byte should be cached as walkable for the rest of the session.
*   **Implementation**:
    *   Add `session_walkable_cache: set[int]` to `CollisionGrid`.
    *   Update `is_walkable()` to also check this cache.
    *   Expose MCP tool `report_walkable_tile(x, y)` that the Agent calls after a successful `visual_guided_step` onto a "blocked" tile. The tool reads the collision byte and adds it to the cache.
*   **Acceptance Criteria**: After an Agent bumps onto a "blocked" grass tile successfully, all other tiles with the same byte are automatically treated as walkable for the rest of the session.

---

## 💾 State & Memory (STATE)

### [STATE-001] Implement `get_game_state_flags`
**Goal**: Read "Story Progress" from RAM.
*   **File**: `src/game_state.py` (New or update existing)
*   **Research**:
    *   Pallet Town Events: `0xD747` - `0xD74E` (Event Flags).
    *   Starters: `0xD710` (Script flags).
*   **Implementation**:
    *   Return a dictionary: `{"oak_parcel_delivered": bool, "rival_fought": bool}`.
*   **Acceptance Criteria**: Agent knows it has finished the Lab segment without guessing.

---

## 🗣️ User Experience (UX)

### [UX-001] Advanced Dialogue Handling
**Goal**: Handle "Yes/No" and "Naming" screens better.
*   **File**: `src/emulator.py` -> `advance_dialogue`
*   **Implementation**:
    *   Detect the "Arrow" cursor in the text box (Yes/No choice).
    *   Stop mashing and return: "Prompt Active: [Yes] No".
*   **Acceptance Criteria**: Agent stops at "Do you want to name this Pokemon?" instead of selecting "No" accidentally.

---

## 🧹 Maintenance (MAINT)

### [MAINT-001] General Codebase Cleanup & Refactor
**Goal**: Improve code quality, readability, and maintainability for future contributors.
*   **Files**: All (`server.py`, `src/*.py`, `constants.py`)
*   **Priority**: Complete **last**, after all functional tickets are done.
*   **Scope**:
    *   **`server.py`**: The `process_command` dispatch function is a 100+ line `if/elif` chain. Refactor to a command registry (dict mapping names to handler functions).
    *   **`src/navigation.py`**: At ~780 lines, this file is doing too much. Split into focused modules:
        *   `src/pathfinder.py` — A* algorithm and path utilities.
        *   `src/navigation.py` — Movement execution, `walk_to`, `interact_with`.
        *   `src/world_memory.py` — Warp tracking, tile memory, world knowledge.
    *   **`src/constants.py`**: Group constants logically (RAM addresses, tile maps, button maps) and add docstring headers for each section. Remove dead/duplicate entries.
    *   **`src/emulator.py`**: Extract dialogue handling (`advance_dialogue`, `get_dialogue_text`, `is_dialogue_active`) into a dedicated `src/dialogue.py` module.
    *   **General**: Add type hints, consistent docstrings, and remove dead code (commented-out `walk_to` tool in `server.py`, unused `_world_memory` references in `navigation.py`).
*   **Acceptance Criteria**: Each `src/` module is under ~300 lines, `server.py` dispatch is a clean registry, and a new developer can understand the architecture in 15 minutes.

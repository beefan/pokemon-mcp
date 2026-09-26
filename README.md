# Pokémon Blue Strategic MCP Server

An **MCP (Model Context Protocol)** server that enables autonomous AI agents (Antigravity, Claude, Codex, etc.) to play **Pokémon Blue (Game Boy)** via a streamlined, deterministic, vision-first interface.

---

## 🌟 Overview

Previous AI Game Boy agents often struggled with navigation and stalled in loops because they relied on fragile reverse-engineered collision tables, inaccurate A\* pathfinders, or noisy OCR overlays.

This server redesigns agent interaction around **three core principles**:

1. **Vision-First, Ground-Truth Perceptual Space**: Provides clean, unobscured 4× nearest-neighbor screenshots (`640x576`) paired with direct Game Boy tilemap ASCII extraction (`screen_text`) for 100% reliable text and menu perception without OCR errors or latency.
2. **The Game Boy is the Physics Engine**: Rather than re-implementing collision and pathfinding in Python, the emulator (PyBoy) simulates authentic Z80 hardware collision, ledges, and scripts.
3. **Minimal, Orthogonal Tool Surface**: Consolidates control into **5 high-leverage tools** designed for deterministic decision-making.

---

## 🎮 Exposed Tools

| Tool                                      | Purpose                                                                                                                                                   | Arguments                                                                           | Key Returns                                                                                                                                                              |
| :---------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`get_state()`**                         | Primary sensory tool. Returns clean 4× upscaled screenshot (`640x576`) + ground-truth tilemap text + telemetry.                                           | None                                                                                | `image_path`, `screen_text`, `map_id`, `map_name`, `position` `[x, y]`, `in_battle`, `dialogue_active`, `menu_active`                                                    |
| **`step(direction, count)`**              | Verified cardinal movement across the overworld. Respects Gen 1's 16-frame movement grid and turn delay. Halts on obstacles, battles, warps, or dialogue. | `direction` (`"up"`, `"down"`, `"left"`, `"right"`), `count` (1–10, default 1)      | `steps_completed`, `final_position`, `final_map`, `map_id`, `interrupted_by` (`"hit_obstacle"`, `"battle_started"`, `"map_transition"`, `"dialogue_started"`, or `null`) |
| **`press(buttons, delay_frames)`**        | Fine-grained button execution for menus, naming, battles, and interacting with adjacent objects/NPCs.                                                     | `buttons` (e.g. `["a"]`, `["down", "a"]`, `["start"]`), `delay_frames` (default 15) | `presses`, updated `screen_text`, `in_battle`, `dialogue_active`, `menu_active`                                                                                          |
| **`advance_dialogue(max_pages)`**         | Fast-forwards through multi-page NPC speech and cutscenes. Captures every page into an ASCII transcript. Halts immediately on prompts or closure.         | `max_pages` (1–10, default 5)                                                       | `pages` (list of transcript pages), `status` (`"dialogue_closed"` or `"prompt_detected"`)                                                                                |
| **`save_game(name)` / `load_game(name)`** | Reliable emulator state checkpointing and recovery.                                                                                                       | `name` (e.g. `"before_brock"`, `"viridian_city"`)                                   | Confirmation string                                                                                                                                                      |

---

## 🛠️ Setup & Installation

### 1. Prerequisites

- **Python 3.10+** (tested on Python 3.12 and 3.13)
- **Game Boy ROM**: You must provide your own legally obtained ROM file of _Pokémon Blue_.

### 2. Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/beefan/pokemon-mcp.git
   cd pokemon-mcp
   ```

2. **Initialize Virtual Environment**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **ROM Placement**:
   Place your Pokémon Blue ROM in the project root and name it `PokemonBlue.gb`:

   ```bash
   ls PokemonBlue.gb
   ```

4. **Verify Tests**:
   Run the test suite to verify emulator and tool functionality:
   ```bash
   ./.venv/bin/python -m unittest discover tests
   ```

---

## 🤖 MCP Client Configuration

### Antigravity / Gemini CLI (`mcp_config.json` or `settings.json`)

Add the server under `mcpServers`:

```json
{
  "mcpServers": {
    "pokemon-blue": {
      "command": "/absolute/path/to/pokemon-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/pokemon-mcp/server.py"],
      "env": {
        "HEADLESS": "false"
      }
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "pokemon-blue": {
      "command": "/absolute/path/to/pokemon-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/pokemon-mcp/server.py"],
      "env": {
        "HEADLESS": "false"
      }
    }
  }
}
```

> [!TIP]
>
> - Set `"HEADLESS": "false"` to open the native SDL2 emulator window and watch the AI play in real time.
> - Set `"HEADLESS": "true"` for maximum emulation speed and headless operation (e.g. on remote servers).

---

## 🧭 Playing the Game

The agent is guided by [`MISSION.md`](MISSION.md), which provides campaign milestones from Pallet Town through the Elite Four:

1. **Sensory Loop**: The agent inspects visual reality using `get_state()`.
2. **Cardinal Navigation**: Overworld movement uses `step("direction", count)`. If the player bumps into a wall, enters a doorway, encounters a Pokémon, or triggers an NPC, `step` halts safely and reports the event.
3. **Dialogue Clearance**: Cutscenes and speech are fast-forwarded with `advance_dialogue()`, which automatically captures page transcripts and halts on choice prompts (YES/NO, naming, starter selection).
4. **Menus & Combat**: Battles, item use, and party menus are operated deterministically using `press(["buttons"])`.

---

## 💻 Tech Stack

- **MCP Framework**: [FastMCP](https://github.com/jlowin/fastmcp) (Python)
- **Emulator Core**: [PyBoy](https://github.com/Baekalfen/PyBoy) (Cycle-accurate Game Boy emulation)
- **Imaging**: [Pillow](https://python-pillow.org/) (Nearest-neighbor 4× scaling to 640×576)
- **ROM Target**: _Pokémon Blue_ (Game Boy, US / English release)

---

## ⚖️ Legal Disclaimer

This project is an automation interface for Game Boy emulation research. It does **not** distribute or include Nintendo software, ROMs, or copyrighted game assets.

- **You must supply your own legally acquired ROM file.**
- Pokémon is a registered trademark of Nintendo, Creatures Inc., and GAME FREAK inc. This project is unaffiliated with, unauthorized by, and unendorsed by Nintendo or GAME FREAK.

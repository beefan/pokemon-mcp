# Pokémon Blue Strategic MCP Server

> [!WARNING]
> **Project Status: Abandoned (Active Archive)**  
> This project is currently on pause. While the tactical interface and RAM monitoring are robust, AI agents (Antigravity, etc.) struggle immensely with the nuanced navigation required for Pokémon Blue. Despite frequent improvements to the A* pathfinding and collision tools, agents often waste excessive tokens walking in circles or failing to navigate simple obstacles. I am "giving up" on this for now, but leaving the code as a reference for MCP development in complex environments.

> [!NOTE]
> **AI Authorship Disclaimer**  
> This codebase was primarily generated and modified using AI coding assistants (**Antigravity**, **GeminiCLI**, and **codex**). As such, you may encounter "garbage" code, redundant logic, or experimental scaffolding that remains in the repository.

## 🌟 Overview
An **MCP (Model Context Protocol)** server that acts as a tactical interface for Pokémon Blue (GameBoy). it enables an LLM agent to play the game by issuing high-level strategic commands while the server handles the frame-perfect execution and RAM monitoring.

---

## 🚀 Features
- **Tactical Interface**: Abstracts low-level button presses into high-level commands like `walk_to(x, y)` and `execute_battle_turn()`.
- **Memory-Driven Vision**: Provides screenshots (`get_screen_analysis`) with coordinate overlays and OCR to help the agent "see".
- **Collision Intelligence**: Real-time RAM inspection of collision maps to determine walkability accurately.
- **Auto-Checkpointing**: Automatically saves game state before major actions to allow for easy recovery.
- **Save/Load States**: Full management of emulator states for retrying strategies.
- **Journaling**: A persistent memory system (`game_journal.json`) to track progress between sessions.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- **Python 3.10+** (tested with Python 3.12)
- **GameBoy ROM**: You must provide your own legally obtained ROM file of *Pokémon Blue*.

### 2. Installation
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/beefan/pokemon-mcp.git
    cd pokemon-mcp
    ```
2.  **Initialize Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **ROM Placement**:
    Place your Pokémon Blue ROM in the root directory and rename it to `PokemonBlue.gb`.

4.  **Mission Setup**:
    Ensure `MISSION.md` is present in the root. This is the primary instruction file the agent reads to understand its goals.

### 3. Running the Server

While you can run the server manually, it is designed to be managed by your AI coding agent. This ensures the server starts automatically when you begin a session and environment variables (like `HEADLESS`) are set correctly.

#### Codex Integration (`~/.codex/config.toml`)
Add the following to your Codex configuration:
```toml
[mcp_servers.pokemon-blue]
command = "/path/to/pokemon-mcp/.venv/bin/python"
args = ["/path/to/pokemon-mcp/server.py"]

[mcp_servers.pokemon-blue.env]
HEADLESS = "false"  # Set to "true" for faster, windowless execution
```

#### Gemini CLI Integration (`~/.gemini/settings.json`)
Add the following to your `mcpServers` block:
```json
"pokemon-blue": {
  "command": "/path/to/pokemon-mcp/.venv/bin/python",
  "args": [
    "/path/to/pokemon-mcp/server.py"
  ],
  "env": {
    "HEADLESS": "false"
  }
}
```

## 🎮 Exposed Tools

| Tool | Description |
| :--- | :--- |
| `get_screen_analysis` | **Primary Vision**. Returns a screenshot with a coordinate grid overlay. |
| `get_player_status` | Returns current Map ID, (X, Y) coordinates, and nearby POIs. |
| `walk_to(x, y)` | Navigates to a specific map coordinate using A* pathfinding. |
| `move_direction(dir, steps)` | Moves the player in a cardinal direction for X steps. |
| `interact_with(x, y)` | Walks to and interacts with an object (NPC, Item, PC). |
| `advance_dialogue` | Mashes A/B buttons until the current text box/dialogue is cleared. |
| `execute_battle_turn` | issues high-level battle commands (Attack, Switch, Item). |
| `get_party_info` | Returns current Pokémon team stats (HP, Level, Moves). |
| `get_collision_grid` | Returns a boolean grid of walkable tiles centered on the player. |
| `save_game / load_game` | Captures or restores the full emulator state. |
| `read_journal` | Accesses the persistent `game_journal.json` for task tracking. |

---

## 💻 Tech Stack
- **Framework**: [FastMCP](https://github.com/jlowin/fastmcp) (Python)
- **Emulator**: [PyBoy](https://github.com/Baekalfen/PyBoy)
- **Logic**: Custom A* implementation and RAM address mapping for Gen 1 Pokémon.

## ⚖️ Legal Disclaimer
This project is an automation tool for GameBoy emulation. It does **not** include any Nintendo software, ROMs, or copyrighted assets.
- **You must provide your own ROM file.**
- Pokémon is a trademark of Nintendo/Creatures Inc./GAME FREAK inc. This project is not affiliated with or endorsed by Nintendo.

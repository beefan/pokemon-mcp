# Pokémon Blue Strategic MCP Server

An **MCP (Model Context Protocol)** server that acts as a tactical interface for Pokémon Blue (GameBoy). It enables an LLM agent to play the game by issuing high-level strategic commands while the server handles the frame-perfect execution and RAM monitoring.

## 🚀 Features
- **Tactical Interface**: Abstracts low-level button presses into commands like `walk_to(x, y)`, `execute_battle_turn()`.
- **Visual Intelligence**: Provides screenshots (`get_screen_analysis`) and OCR text to let the agent "see" the game.
- **Auto-Navigation**: A* pathfinding with configurable policies for handling encounters and obstacles.
- **Save/Load States**: Instant savestate management for retrying risky strategies.
- **The Journal & Mission Control**: A persistent memory system that loads mission-critical instructions from `MISSION.md`.

## 🛠️ Setup

### 1. Prerequisites
- **Python 3.10+**
- **GameBoy ROM**: You must provide your own legally obtained ROM file of *Pokémon Blue*. 

### 2. Installation
1. Clone the repository and install dependencies:
```bash
git clone https://github.com/your-username/og-pokemon-mcp.git
cd og-pokemon-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. File Placement (CRITICAL)
For the MCP server to work correctly, specific files must be present in the **working directory where the LLM agent is run**:

1.  **ROM**: Place your Pokémon Blue ROM in that directory and rename it to `PokemonBlue.gb`.
2.  **Mission Control**: Copy `MISSION.md` from this project into that same directory. The agent uses this file to initialize its goals. You can customize this file to give the agent specific instructions.

## 🎮 Tools provided to the Agent

| Tool | Purpose |
| :--- | :--- |
| `get_local_map` | Returns Map ID, (X,Y) coords, and an ASCII tile grid. |
| `walk_to(x, y)` | Moves the player to coordinates using A* pathfinding. |
| `get_screen_analysis` | Captures screen & overlays a grid with coordinates. Use this to see the world. |
| `advance_dialogue` | Mashes A/B to clear text. Includes loop and naming screen detection. |
| `press_buttons(seq)` | Macro for sequences like `'start, wait, a'`. |
| `save_game / load_game` | Instantly capture or restore the emulator state. |
| `read_journal` | Access the agent's persistent task list and mission notes. |
| `read_ram_region` | Direct memory inspection for debugging flags. |

## 💻 Running the Server

### Default (Headless Mode)
Start the MCP server directly:
```bash
./.venv/bin/python server.py
```

### GUI Mode (Watch the AI play)
To watch the emulation window live:
```bash
# MacOS/Linux
HEADLESS=false ./.venv/bin/python server.py
```

## ⚖️ Legal Disclaimer
This project is an automation tool for GameBoy emulation. It does **not** include any Nintendo software, ROMs, or copyrighted assets.
- **You must provide your own ROM file.**
- Pokémon is a trademark of Nintendo/Creatures Inc./GAME FREAK inc. This project is not affiliated with or endorsed by Nintendo.

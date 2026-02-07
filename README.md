# Pokémon Blue Strategic MCP Server

An **MCP (Model Context Protocol)** server that acts as a tactical interface for Pokémon Blue (GameBoy). It enables an LLM agent to play the game by issuing high-level strategic commands while the server handles the frame-perfect execution and RAM monitoring.

## 🚀 Features
- **Tactical Interface**: Abstracts low-level button presses into commands like `walk_to(Viridian)`, `attack()`, `switch_pokemon()`.
- **Visual Context**: Provides the agent with a local map grid read directly from VRAM.
- **Auto-Navigation**: A* pathfinding with configurable policies for handling wild encounters (Fight, Run, or Interrupt).
- **State Persistence**: Memory system for the agent to log goals and strategy notes.

## 🛠️ Setup

### 1. Prerequisites
- **Python 3.10+** (Tested with 3.13)
- **GameBoy ROM**: You must provide your own legally obtained ROM file of *Pokémon Blue*. This project does **not** distribute copyrighted material.

### 2. Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/og-pokemon-mcp.git
cd og-pokemon-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. ROM Setup
1. Dump your own Pokémon Blue cartridge or obtain the ROM legally.
2. Rename the file to `PokemonBlue.gb`.
3. Place `PokemonBlue.gb` in the root directory of this project.

## 🎮 Usage

### Running the Server
Start the MCP server using the provided wrapper script (or directly via python):

```bash
# Default (Headless Mode)
./.venv/bin/python server.py
```

### Configuration (Headless vs. GUI)
By default, the emulator runs in **headless mode** (no window) to run efficiently on servers or background processes.

To watch the AI play (GUI mode):
```bash
# MacOS/Linux
HEADLESS=false ./.venv/bin/python server.py
```

### Connecting an LLM
This project uses **stdio** mode by default, meaning the MCP client (like Claude Desktop) runs the python script itself. You do **not** need to run a separate server process in a terminal window for the client to connect to.

#### Claude Desktop App
1. Open `~/Library/Application Support/Claude/claude_desktop_config.json`.
2. Add the server configuration (this tells Claude how to launch the server):
```json
{
  "mcpServers": {
    "pokemon-blue": {
      "command": "/absolute/path/to/og-pokemon-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/og-pokemon-mcp/server.py"],
      "env": {
        "HEADLESS": "false" 
      }
    }
  }
}
```
3. Restart Claude Desktop.
4. You can now ask Claude: *"Check the current map and walk me to the nearest city."*

## ⚖️ Legal Disclaimer
This project is an automation tool for the GameBoy hardware/emulation. It does **not** include any Nintendo software, ROMs, or copyrighted assets.
- **You must provide your own ROM file.**
- Users are responsible for complying with their local laws regarding ROM dumping and emulation. 
- Pokémon is a trademark of Nintendo/Creatures Inc./GAME FREAK inc. This project is not affiliated with or endorsed by Nintendo.

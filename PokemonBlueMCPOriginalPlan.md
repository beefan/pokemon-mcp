🎮 Project: Pokémon Blue Strategic MCP
🎯 Objective

Create an MCP server that acts as a Tactical Interface for Pokémon Blue. The AI agent should function as a "Commanding Officer," issuing high-level strategic orders while the MCP server handles the frame-perfect execution and RAM-based monitoring.
🏗️ Technical Stack

    Emulator: PyBoy (with PokemonBlue.gb ROM).

    Framework: FastMCP (Python).

    Navigation: Constrained A* Pathfinding (limited to the current map).

    Automation: Battle Macro Engine (handles menu navigation for Run/Attack/Switch).

🛠️ MCP Tool Definitions
1. Constrained Navigation

    get_local_map(): Returns a 20x18 text-based grid (ASCII) of the current screen tiles (e.g., W for wall, D for door, P for player).

    walk_to(x, y, on_battle: str): Moves the player to a coordinate within the current map.

        on_battle="interrupt": (Default) Stops and returns control to LLM if a battle starts.

        on_battle="run": Automatically attempts to escape wild battles and continues walking.

        on_battle="spam_attack": Uses the first move until the battle is won, then continues walking.

2. Strategic Battle Control

    execute_battle_turn(action: str): High-level battle commands.

        action="fight_slot_1": Navigates menus to use the first move.

        action="switch_pokemon(slot)": Navigates menus to swap.

        action="use_item(item_id)": Automates item usage in battle.

3. State & Memory (The "Journal")

    read_journal(): Returns a summary of the game_journal.json. This is the agent's first step after context collapse.

    write_journal_entry(note: str): Persistent log of progress (e.g., "Defeated Misty. Starmie is dangerous, used Sleep Powder strategy.").

🧬 System Architecture: The "Commanding Officer" Loop

    Observation: LLM calls get_local_map() and get_party_stats().

    Strategy: LLM decides to move to the next city and sets a run policy for battles to conserve HP.

    Execution: The MCP server handles the "A" button mashing and directional inputs.

    Event: If a trainer (un-skippable) intercepts the player, the server stops and reports: "Interrupted! Trainer battle started. Policy 'run' is invalid for trainer battles. Awaiting orders."

📋 Critical RAM Addresses for Agents
Address	Purpose	Value Mapping
0xD362	Player X-Coord	0-255
0xD361	Player Y-Coord	0-255
0xD35E	Current Map ID	Map index (e.g., 0=Pallet Town)
0xD057	Enemy HP	0 = Out of battle
0xD11B	Dialogue State	0x01 = Text box active
0xD163	Party Count	Number of Pokémon in team
🚀 Implementation Roadmap for AutoGravity Agents

    Pathfinder Implementation: Build a local A* script that reads PyBoy's tilemap to identify walkable vs. non-walkable tiles.

    Dialogue Handler: Create a utility that checks 0xD11B and pulses the A button until the address clears, returning the aggregated text.

    The "Strategy Engine": Implement the on_battle logic within the walk_to loop. Use pyboy.tick() inside a while loop to monitor RAM every frame during movement.

    Persistence: Initialize game_journal.json with the player's name and starter choice.

import heapq
from src.emulator import PokemonEmulator
from src.constants import *

class Navigation:
    def __init__(self, emulator: PokemonEmulator, battle_engine=None):
        self.emulator = emulator
        self.battle_engine = battle_engine

    def get_local_map(self):
        """
        Returns a dictionary containing map_id, position, and the grid.
        """
        map_id = self.emulator.get_map_id()
        x, y = self.emulator.get_player_position()
        
        # Placeholder grid logic
        # Ideally, we read the map data from memory or VRAM.
        # Given limitations, we might need a known map layout or heuristic.
        # For this phase, let's just return a basic grid around the player.
        
        grid = self._scanner_local_grid(x, y)
        
        return {
            "map_id": map_id,
            "position": (x, y),
            "grid": grid
        }

    def _scanner_local_grid(self, px, py):
        """
        Scans the local area around the player using PyBoy's tilemap helper.
        """
        # PyBoy's tilemap_window gives us the 20x18 grid of tile IDs currently on screen.
        # We need to expose this from the emulator wrapper first.
        # For now, let's assume we add get_screen_tiles() to emulator.py
        
        # If we can't access it easily, we can stick to coordinates. 
        # But the requirement is a grid string.
        
        try:
            # Get the raw tile IDs from the emulator VRAM
            tile_ids = self.emulator.get_screen_tile_ids() # 20x18 matrix
            
            grid_str = []
            for y in range(18):
                row = ""
                for x in range(20):
                     tid = tile_ids[x][y] & 0xFF # Mask to 8-bit tile ID
                     # Map ID to Char if known, else relative symbols
                     char = TILE_MAP.get(tid, None)
                     if char is None:
                         char = f"{tid:02X}" if tid != 0 else "."
                     row += char + " "
                grid_str.append(row.strip())
            return "\n".join(grid_str)
        except Exception as e:
            return f"Error reading grid: {e}\n(Player at {px}, {py})"

    def find_path(self, start_pos, target_pos, known_walls=set(), max_nodes=500):
        """
        A* pathfinding with a node limit to prevent hangs.
        """
        if start_pos == target_pos:
            return []
            
        open_set = []
        heapq.heappush(open_set, (0, start_pos))
        came_from = {}
        g_score = {start_pos: 0}
        f_score = {start_pos: self._heuristic(start_pos, target_pos)}
        
        nodes_explored = 0
        while open_set and nodes_explored < max_nodes:
            nodes_explored += 1
            current = heapq.heappop(open_set)[1]
            
            if current == target_pos:
                return self._reconstruct_path(came_from, current)
                
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if neighbor in known_walls:
                    continue
                    
                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f = tentative_g_score + self._heuristic(neighbor, target_pos)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))
                    
        return None # No path found or limit reached

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        total_path.reverse()
        return total_path[1:] # Exclude start

    def walk_to(self, target_x, target_y, on_battle="interrupt", max_steps=50):
        """
        Navigate to target coordinates.
        Returns reason for stopping: "arrived", "battle", "blocked", "interrupted", "max_steps"
        """
        if self.emulator.is_dialogue_active():
             return "stopped: dialogue is active. Use advance_dialogue() or press 'a' to clear text before walking."

        known_walls = set()
        steps_taken = 0
        
        while steps_taken < max_steps:
            # 1. Update State
            current_x, current_y = self.emulator.get_player_position()
            current_pos = (current_x, current_y)
            target_pos = (target_x, target_y)
            
            if current_pos == target_pos:
                return "arrived"
                
            # 2. Populate walls from screen if possible (Optimization)
            # This helps A* find paths faster by avoiding obvious on-screen obstacles
            try:
                tile_ids = self.emulator.get_screen_tile_ids()
                # We don't know the exact global coords of screen tiles without more calc,
                # but we can at least detect the one we are about to step on.
            except:
                pass

            # 3. Check for Battle
            enemy_hp = self.emulator.read_ram(ENEMY_HP_ADDR)
            if enemy_hp > 0:
                # Battle detected!
                if on_battle == "interrupt":
                    return "battle_started"
                elif on_battle == "run":
                    if self.battle_engine:
                        self.battle_engine.run_away()
                        # Allow some time for state change
                        self.emulator.tick(60)
                        # Check if battle ended
                        if self.emulator.read_ram(ENEMY_HP_ADDR) == 0:
                            continue # Escaped! Continue walking.
                        else:
                            return "battle_trapped" # Failed to run
                    else:
                        return "error: no battle engine"
                elif on_battle == "spam_attack":
                    if self.battle_engine:
                        self.battle_engine.attack()
                        self.emulator.tick(60) 
                        # We need a loop here for spam attack, but doing one turn per walk step is weird.
                        # The prompt says: "Uses the first move until the battle is won".
                        # This implies a blocking loop.
                        while self.emulator.read_ram(ENEMY_HP_ADDR) > 0:
                            self.battle_engine.attack()
                            self.emulator.tick(120) 
                            # Check if we died? 
                            if self.emulator.read_ram(PARTY_COUNT_ADDR) == 0: # simplified death check
                                return "blacked_out"
                        continue # Won!
                    else:
                        return "error: no battle engine"
                else:
                    return f"unknown policy: {on_battle}"

            # 4. Pathfind
            path = self.find_path(current_pos, target_pos, known_walls)
            if not path:
                return "blocked: no path found"
                
            next_step = path[0]
            dx = next_step[0] - current_x
            dy = next_step[1] - current_y
            
            # 5. Execute Move
            button = None
            if dy == -1: button = BUTTON_UP
            elif dy == 1: button = BUTTON_DOWN
            elif dx == -1: button = BUTTON_LEFT
            elif dx == 1: button = BUTTON_RIGHT
            
            if button:
                self.emulator.input(button, hold_frames=5) # Faster input
                steps_taken += 1
                
            # 6. Verify Move
            new_x, new_y = self.emulator.get_player_position()
            if (new_x, new_y) == current_pos:
                # We didn't move. Blocked!
                known_walls.add(next_step)
            
            # Periodic tick to keep emulator healthy
            self.emulator.tick(1)
            
        return "max_steps_reached"

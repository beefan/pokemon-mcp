import heapq
from src.emulator import PokemonEmulator
from src.constants import *

DIRECTION_TO_BUTTON = {
    "up": BUTTON_UP,
    "down": BUTTON_DOWN,
    "left": BUTTON_LEFT,
    "right": BUTTON_RIGHT
}
class Navigation:
    def __init__(self, emulator: PokemonEmulator, battle_engine=None):
        self.emulator = emulator
        self.battle_engine = battle_engine
        self._collision_cache = {}
        self._last_scan_origin = None

    def get_local_map(self):
        """
        Returns a dictionary containing map_id, position, and the grid.
        Includes a legend, nearby warps, and identified objects.
        """
        map_id = self.emulator.get_map_id()
        x, y = self.emulator.get_player_position()
        
        grid_data = self._scanner_local_grid_data(x, y)
        grid_str = grid_data["grid_str"]
        objects = grid_data["objects"]
        collision_map = grid_data["collision"]
        self._cache_collision_map(x, y, collision_map)
        warps = self._find_on_screen_warps()
        
        serializable_collision = {
            f"{pos[0]},{pos[1]}": data for pos, data in collision_map.items()
        }
        return {
            "map_id": map_id,
            "position": (x, y),
            "grid": f"{grid_str}\n\nLegend: {GRID_LEGEND}",
            "nearby_warps": warps,
            "nearby_objects": objects,
            "collision_map": serializable_collision
        }

    def _scanner_local_grid_data(self, px, py):
        """
        Scans the local area around the player.
        Returns a dict with grid string, nearby objects, and detailed collision metadata.
        """
        try:
            # Get the raw tile IDs from the emulator VRAM
            tile_ids = self.emulator.get_screen_tile_ids() # 20x18 matrix
            
            # 1. Column Headers (X coordinates)
            col_headers = "    " # Padding for row labels
            for x in range(20):
                abs_x = px + (x - 10)
                col_headers += f"{abs_x:2} "
            
            grid_rows = [col_headers]
            found_objects = []
            collision_map = {}
            
            # 2. Rows with labels
            for y in range(18):
                abs_y = py + (y - 9)
                row_label = f"{abs_y:2} | "
                row_chars = []
                for x in range(20):
                    tid = tile_ids[x][y] & 0xFF
                    # Map ID to Char if known
                    char = TILE_MAP.get(tid, None)
                    
                    # Global coords
                    gx, gy = px + (x - 10), py + (y - 9)

                    if char is None:
                        # Default to hex ID for unknown tiles so agent can still "see" them
                        char = f"{tid:02X}" if tid != 0 else ".."
                    
                    # Object Detection
                    if char == "o":
                        found_objects.append({"name": "Pokéball", "pos": (gx, gy)})
                    elif char == "P" or char == "M":
                        found_objects.append({"name": "Pokemon Symbol", "pos": (gx, gy)})

                    walkable = self._char_is_walkable(char)
                    collision_map[(gx, gy)] = {
                        "char": char,
                        "tid": tid,
                        "name": TILE_NAMES.get(char, "Unknown"),
                        "walkable": walkable
                    }

                    row_chars.append(f"{char:2}")
                grid_rows.append(row_label + " ".join(row_chars))
            
            return {
                "grid_str": "\n".join(grid_rows),
                "objects": found_objects,
                "collision": collision_map
            }
        except Exception as e:
            return {
                "grid_str": f"Error reading grid: {e}\n(Player at {px}, {py})",
                "objects": [],
                "collision": {}
            }

    def _cache_collision_map(self, px, py, collision_map):
        self._collision_cache = collision_map
        self._last_scan_origin = (px, py)

    def _refresh_collision_cache(self):
        """
        Re-scan the current screen and refresh the cached collision data
        so navigation helpers can rely on up-to-date walkability info.
        """
        px, py = self.emulator.get_player_position()
        grid_data = self._scanner_local_grid_data(px, py)
        self._cache_collision_map(px, py, grid_data["collision"])

    def _get_collision_tile(self, pos):
        return self._collision_cache.get(pos)

    def _char_is_walkable(self, char):
        if not char:
            return True
        if char in WALKABLE_CHARS:
            return True
        if char in {".."}:
            return True
        if isinstance(char, str) and char.startswith("ID:"):
            return True
        return False

    def _is_tile_walkable(self, pos):
        tile = self._get_collision_tile(pos)
        if not tile:
            return True
        return tile.get("walkable", True)

    def _adjacent_walkable_positions(self, target_x, target_y):
        adjacents = [
            (target_x, target_y - 1, "down"),
            (target_x, target_y + 1, "up"),
            (target_x - 1, target_y, "right"),
            (target_x + 1, target_y, "left")
        ]
        return [t for t in adjacents if self._is_tile_walkable((t[0], t[1]))]

    def _warp_at_position(self, pos):
        for warp in self._find_on_screen_warps():
            if warp["pos"] == pos:
                return warp
        return None

    def _closest_warp_approach(self, warp_pos, current_pos):
        approaches = self._adjacent_walkable_positions(*warp_pos)
        if not approaches:
            return None
        approaches.sort(key=lambda p: abs(p[0] - current_pos[0]) + abs(p[1] - current_pos[1]))
        return approaches[0]

    def _attempt_warp_entry(self, direction, warp_pos):
        """
        Presses the direction needed to step into a warp and returns True if the player
        either arrives on the warp tile or the map ID changes (meaning a transition happened).
        """
        button = DIRECTION_TO_BUTTON.get(direction)
        if not button:
            return False

        prev_map = self.emulator.get_map_id()
        prev_pos = self.emulator.get_player_position()

        self.emulator.input(button, hold_frames=8)
        self.emulator.tick(15)

        post_map = self.emulator.get_map_id()
        post_pos = self.emulator.get_player_position()

        return post_map != prev_map or post_pos == warp_pos

    def _direction_to_target(self, src, target):
        dx = target[0] - src[0]
        dy = target[1] - src[1]
        if abs(dx) + abs(dy) != 1:
            return None
        if dx == 1:
            return "right"
        if dx == -1:
            return "left"
        if dy == 1:
            return "down"
        if dy == -1:
            return "up"
        return None

    def _find_on_screen_warps(self):
        """
        Scans VRAM for stairs (S) and doors (>). 
        Returns a list of warp objects with coordinates and suggested entry directions.
        """
        warps = []
        try:
            tiles = self.emulator.get_screen_tile_ids()
            # Player is at (10, 9)
            px, py = self.emulator.get_player_position()
            
            for tx in range(20):
                for ty in range(18):
                    tid = tiles[tx][ty] & 0xFF
                    char = TILE_MAP.get(tid)
                    if char in ["S", ">"]:
                        # Convert screen to global map coords
                        # Screen center (10,9) is player pos (px, py)
                        gx = px + (tx - 10)
                        gy = py + (ty - 9)
                        
                        target_direction = "unknown"
                        if char == ">": target_direction = "up" # Doors usually require walking up
                        elif char == "S": 
                            # Stairs logic depends on visual
                            target_direction = "into it" 
                            
                        warps.append({
                            "type": "Stairs" if char == "S" else "Door",
                            "pos": (gx, gy),
                            "required_direction": target_direction
                        })
        except:
            pass
        return warps

    def describe_tile(self, x, y, coordinate_type="screen"):
        """
        Describes a tile. Defaults to screen coords (0-19, 0-17).
        If coordinate_type="map", it calculates screen pos relative to player.
        """
        if coordinate_type == "map":
            px, py = self.emulator.get_player_position()
            sx = (x - px) + 10
            sy = (y - py) + 9
            if not (0 <= sx < 20 and 0 <= sy < 18):
                return f"Error: Map coordinate ({x}, {y}) is not currently visible on screen."
        else:
            sx, sy = x, y
            
        return self.emulator.describe_tile(sx, sy)

    def find_path(self, start_pos, target_pos, known_walls=None, avoid_positions=None, max_nodes=500):
        """
        A* pathfinding with a node limit to prevent hangs.
        Automatically treats warp tiles as walls UNLESS the target_pos is that warp.
        """
        if start_pos == target_pos:
            return []

        # Defensive defaults for mutable params
        if known_walls is None:
            known_walls = set()
        if avoid_positions is None:
            avoid_positions = set()

        # Scan current screen for warps to avoid
        warps = self._find_on_screen_warps()
        warp_positions = {w['pos'] for w in warps}

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
                
                # COLLISION CHECKS
                if neighbor in known_walls:
                    continue
                if neighbor in avoid_positions:
                    continue

                # AUTOMATIC WARP AVOIDANCE
                # If neighbor is a warp and NOT our target, treat as a wall
                if neighbor in warp_positions and neighbor != target_pos:
                    continue

                if not self._is_tile_walkable(neighbor) and neighbor != target_pos:
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

    def get_player_status(self):
        """
        Returns a human-readable status string of the player's current state.
        """
        map_id = self.emulator.get_map_id()
        x, y = self.emulator.get_player_position()
        
        # Check for nearby special tiles
        nearby = []
        try:
            tiles = self.emulator.get_screen_tile_ids()
            # Check 1 tile radius
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    tid = tiles[10+dx][9+dy] & 0xFF
                    char = TILE_MAP.get(tid)
                    if char == "S": nearby.append("Stairs")
                    elif char == ">": nearby.append("Exit/Door")
        except:
            pass
        
        nearby_str = f" [Nearby: {', '.join(set(nearby))}]" if nearby else ""
        return f"Map ID: {map_id}, Position: ({x}, {y}){nearby_str}"

    def walk_to(self, target_x, target_y, on_battle="interrupt", avoid_positions=None, max_steps=100):
        """
        Navigate to target coordinates.
        avoid_positions: List of (x, y) tuples to steer clear of.
        Returns reason for stopping: "arrived", "battle", "blocked", "interrupted", "max_steps"
        """
        if self.emulator.is_dialogue_active():
             return "stopped: dialogue or menu is active. Clear the screen before walking."

        known_walls = set()
        avoid_set = set(avoid_positions) if avoid_positions else set()
        steps_taken = 0
        
        while steps_taken < max_steps:
            self._refresh_collision_cache()
            # 1. Update State
            current_x, current_y = self.emulator.get_player_position()
            current_pos = (current_x, current_y)
            target_pos = (target_x, target_y)
            warp_info = self._warp_at_position(target_pos)
            path_target = target_pos
            warp_entry_direction = None
            if warp_info:
                approach = self._closest_warp_approach(warp_info["pos"], current_pos)
                if not approach:
                    return f"blocked: warp at {target_pos} has no accessible adjacent tile."
                path_target = (approach[0], approach[1])
                warp_entry_direction = approach[2]

            if warp_entry_direction and current_pos == path_target:
                if self._attempt_warp_entry(warp_entry_direction, target_pos):
                    return f"warped: triggered warp at {target_pos}"
                steps_taken += 1
                continue

            if not warp_entry_direction and current_pos == target_pos:
                return "arrived"
                
            # 2. Pathfind
            # Increased node limit for larger maps or complex paths
            path = self.find_path(current_pos, path_target, known_walls, avoid_set, max_nodes=1000)
            if not path:
                return f"blocked: no path found to ({target_x}, {target_y}) from your current position {current_pos}. Check if you are on an interactive tile (like stairs) and try moving away first."
                
            next_step = path[0]
            dx = next_step[0] - current_x
            dy = next_step[1] - current_y
            
            # 3. Check for Battle
            enemy_hp = self.emulator.read_ram(ENEMY_HP_ADDR)
            if enemy_hp > 0:
                if on_battle == "interrupt":
                    return "battle_started"
                elif on_battle == "run":
                    if self.battle_engine:
                        self.battle_engine.run_away()
                        self.emulator.tick(60)
                        if self.emulator.read_ram(ENEMY_HP_ADDR) == 0:
                            continue 
                        else:
                            return "battle_trapped"
                    else:
                        return "error: no battle engine"
                elif on_battle == "spam_attack":
                    if self.battle_engine:
                        while self.emulator.read_ram(ENEMY_HP_ADDR) > 0:
                            self.battle_engine.attack()
                            self.emulator.tick(120) 
                            if self.emulator.read_ram(PARTY_COUNT_ADDR) == 0:
                                return "blacked_out"
                        continue 
                    else:
                        return "error: no battle engine"
                else:
                    return f"unknown policy: {on_battle}"
            
            # 4. Execute Move
            button = None
            if dy == -1: button = BUTTON_UP
            elif dy == 1: button = BUTTON_DOWN
            elif dx == -1: button = BUTTON_LEFT
            elif dx == 1: button = BUTTON_RIGHT
            
            if button:
                self.emulator.input(button, hold_frames=5)
                self.emulator.tick(5) # Stabilization
                steps_taken += 1
                
            # 5. Verify Move
            new_pos = self.emulator.get_player_position()
            if new_pos == current_pos:
                # We didn't move. Try "Lateral Recovery" to unstick!
                # Identify perpendicular directions to the target move
                perps = []
                if button in [BUTTON_UP, BUTTON_DOWN]:
                    perps = [BUTTON_LEFT, BUTTON_RIGHT]
                else:
                    perps = [BUTTON_UP, BUTTON_DOWN]
                
                # Perform lateral tap
                self._lateral_recovery(perps)
                
                # Retry the move with a DEEP press (longer hold)
                self.emulator.input(button, hold_frames=20)
                self.emulator.tick(20)
                new_pos = self.emulator.get_player_position()
                
                if new_pos == current_pos:
                    # Still blocked after recovery. Fail.
                    try:
                        tiles = self.emulator.get_screen_tile_ids()
                        # tx, ty relative to player (10, 9)
                        tx, ty = 10 + dx, 9 + dy
                        tid = tiles[tx][ty] & 0xFF
                        char = TILE_MAP.get(tid, f"ID:0x{tid:02X}")
                        return f"blocked: cannot step on {char} at {next_step} even after lateral recovery."
                    except:
                        known_walls.add(next_step)
                        continue
            
            # Periodic tick to keep emulator healthy
            self.emulator.tick(1)
            
        return "max_steps_reached"
    def interact_with(self, target_x, target_y):
        """
        Interacts with an object at (target_x, target_y).
        Logic: Find adjacent tile -> walk_to it -> Face target -> Press A.
        Returns: "interaction_success", "walk_failed", or "no_accessible_path"
        """
        current_x, current_y = self.emulator.get_player_position()
        self._refresh_collision_cache()
        
        # 1. Find all adjacent walkable tiles near the target
        adjacents = self._adjacent_walkable_positions(target_x, target_y)
        if not adjacents:
            return "no_accessible_path: no walkable tile next to target"

        current_pos = (current_x, current_y)
        player_direction = self._direction_to_target(current_pos, (target_x, target_y))
        if player_direction:
            btn_map = {
                "up": BUTTON_UP,
                "down": BUTTON_DOWN,
                "left": BUTTON_LEFT,
                "right": BUTTON_RIGHT
            }
            self.emulator.input(btn_map[player_direction], hold_frames=2)
            self.emulator.tick(2)
            self.emulator.input(BUTTON_A, hold_frames=5)
            self.emulator.tick(5)
            return "interaction_success"

        # 2. Sort by distance from player
        adjacents.sort(key=lambda p: abs(p[0]-current_x) + abs(p[1]-current_y))

        # 3. Try walking to each
        for ax, ay, face_dir in adjacents:
            # Check if tile itself is walkable (simplified)
            # Find path to see if accessible
            path = self.find_path((current_x, current_y), (ax, ay))
            if path is not None:
                res = self.walk_to(ax, ay)
                if res == "arrived":
                    # 4. Face target and press A
                    btn_map = {
                        "up": BUTTON_UP,
                        "down": BUTTON_DOWN,
                        "left": BUTTON_LEFT,
                        "right": BUTTON_RIGHT
                    }
                    self.emulator.input(btn_map[face_dir], hold_frames=2)
                    self.emulator.tick(2)
                    self.emulator.input(BUTTON_A, hold_frames=5)
                    self.emulator.tick(5)
                    return "interaction_success"
        
        return "no_accessible_path: could not reach a tile adjacent to the target."

    def _lateral_recovery(self, perpendicular_btns):
        """
        Attempts to 'un-wedge' the player by tapping directions perpendicular
        to the blocked path.
        """
        for btn in perpendicular_btns:
            # Very brief tap to shift sub-pixel/collision state
            self.emulator.input(btn, hold_frames=2)
            self.emulator.tick(2)

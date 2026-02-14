import heapq
import random
from collections import deque
from src.emulator import PokemonEmulator
from src.constants import *

DIRECTION_TO_BUTTON = {
    "up": BUTTON_UP,
    "down": BUTTON_DOWN,
    "left": BUTTON_LEFT,
    "right": BUTTON_RIGHT
}
class Navigation:
    def __init__(self, emulator: PokemonEmulator, collision_grid, battle_engine=None):
        self.emulator = emulator
        self.battle_engine = battle_engine
        self.collision = collision_grid
        self._world_memory = {}

    def _refresh_collision_cache(self):
        """Clears the internal collision cache if the collision grid supports it."""
        if hasattr(self.collision, "clear_cache"):
            self.collision.clear_cache()

    def _get_collision_tile(self, pos):
        """Returns tile metadata from the collision grid at the given position."""
        x, y = pos
        # Collision grid usually has a method to get tile info
        if hasattr(self.collision, "get_tile_info"):
            return self.collision.get_tile_info(x, y)
        
        # Fallback to a basic check if method is missing
        return {
            "tid": None,
            "char": None,
            "walkable": self.collision.is_walkable(x, y)
        }

    def get_local_grid(self, radius=2):
        """
        Returns a compact square grid around the player with tile metadata.
        radius=2 yields a 5x5 grid centered on the player.
        """
        px, py = self.emulator.get_player_position()
        self._refresh_collision_cache()
        size = radius * 2 + 1
        grid = []
        for dy in range(-radius, radius + 1):
            row = []
            for dx in range(-radius, radius + 1):
                gx, gy = px + dx, py + dy
                tile = self._get_collision_tile((gx, gy))
                if tile:
                    row.append({
                        "pos": (gx, gy),
                        "char": tile.get("char"),
                        "tid": tile.get("tid"),
                        "walkable": tile.get("walkable"),
                    })
                else:
                    row.append({
                        "pos": (gx, gy),
                        "char": None,
                        "tid": None,
                        "walkable": None,
                    })
            grid.append(row)
        return {
            "map_id": self.emulator.get_map_id(),
            "position": (px, py),
            "radius": radius,
            "size": size,
            "grid": grid,
        }

    def get_tile_histogram(self, radius=6):
        """
        Returns counts of tile IDs around the player for quick classification.
        """
        px, py = self.emulator.get_player_position()
        self._refresh_collision_cache()
        counts = {}
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                gx, gy = px + dx, py + dy
                tile = self._get_collision_tile((gx, gy))
                if not tile:
                    continue
                tid = tile.get("tid")
                key = (tid, tile.get("char"), tile.get("walkable"))
                entry = counts.get(key)
                if entry is None:
                    counts[key] = {
                        "tid": tid,
                        "char": tile.get("char"),
                        "walkable": tile.get("walkable"),
                        "count": 1,
                        "sample_pos": (gx, gy),
                    }
                else:
                    entry["count"] += 1
        results = sorted(counts.values(), key=lambda e: e["count"], reverse=True)
        return {
            "map_id": self.emulator.get_map_id(),
            "position": (px, py),
            "radius": radius,
            "tiles": results,
        }

    def get_local_grid_ascii(self, radius=6, show_tid=False, show_walkable=False):
        """
        Returns a compact ASCII grid centered on the player.
        - show_tid: append hex tile IDs per cell (less compact).
        - show_walkable: append walkability flags per cell.
        """
        px, py = self.emulator.get_player_position()
        self._refresh_collision_cache()
        size = radius * 2 + 1

        def fmt_cell(tile):
            if not tile:
                base = "??"
                tid = "??"
                walk = "?"
            else:
                ch = tile.get("char")
                base = ch if isinstance(ch, str) else "?"
                if len(base) == 1:
                    base = base + " "
                elif len(base) > 2:
                    base = base[:2]
                tid = f"{tile.get('tid'):02X}" if tile.get("tid") is not None else "??"
                walk = "Y" if tile.get("walkable") else "N"

            if show_tid and show_walkable:
                return f"{base}{tid}{walk}"
            if show_tid:
                return f"{base}{tid}"
            if show_walkable:
                return f"{base}{walk}"
            return base

        rows = []
        col_headers = "    "
        for dx in range(-radius, radius + 1):
            col_headers += f"{px + dx:3}"
        rows.append(col_headers)

        for dy in range(-radius, radius + 1):
            row_label = f"{py + dy:3} "
            cells = []
            for dx in range(-radius, radius + 1):
                gx, gy = px + dx, py + dy
                tile = self._get_collision_tile((gx, gy))
                cells.append(fmt_cell(tile))
            rows.append(row_label + " ".join(cells))

        legend = "Legend: base=char, tid=hex, walkable=Y/N"
        return {
            "map_id": self.emulator.get_map_id(),
            "position": (px, py),
            "radius": radius,
            "size": size,
            "grid": "\n".join(rows),
            "legend": legend,
        }







    def _get_memory_bucket(self, map_id):
        bucket = self._world_memory.get(map_id)
        if bucket is None:
            bucket = {
                "tiles": {},
                "warps": {}
            }
            self._world_memory[map_id] = bucket
        return bucket

    def _remember_collision_map(self, map_id, collision_map):
        bucket = self._get_memory_bucket(map_id)
        tiles = bucket["tiles"]
        warps = bucket["warps"]
        for pos, data in collision_map.items():
            tiles[pos] = {
                "char": data.get("char"),
                "tid": data.get("tid"),
                "walkable": data.get("walkable")
            }
            ch = data.get("char")
            if ch in ("S", ">"):
                warps[pos] = {
                    "type": "Stairs" if ch == "S" else "Door",
                    "pos": pos,
                    "required_direction": "up" if ch == ">" else "into it"
                }

    def get_known_warps(self, map_id=None):
        if map_id is None:
            map_id = self.emulator.get_map_id()
        bucket = self._get_memory_bucket(map_id)
        return list(bucket["warps"].values())



    def _is_tile_walkable(self, pos):
        """Checks walkability using the definitive collision map data from the CollisionGrid instance."""
        return self.collision.is_walkable(pos[0], pos[1])

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
                is_walkable = self._is_tile_walkable(neighbor)
                
                # COLLISION CHECKS
                if neighbor in known_walls:
                    continue
                if neighbor in avoid_positions:
                    continue

                # AUTOMATIC WARP AVOIDANCE
                # If neighbor is a warp and NOT our target, treat as a wall
                if neighbor in warp_positions and neighbor != target_pos:
                    continue

                if not is_walkable and neighbor != target_pos:
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

    def _path_to_directions(self, start_pos, path):
        directions = []
        current = start_pos
        for step in path:
            dx = step[0] - current[0]
            dy = step[1] - current[1]
            if dx == 1 and dy == 0:
                directions.append("right")
            elif dx == -1 and dy == 0:
                directions.append("left")
            elif dx == 0 and dy == 1:
                directions.append("down")
            elif dx == 0 and dy == -1:
                directions.append("up")
            current = step
        return directions

    def find_path_to(self, target_x, target_y, use_memory=False, max_nodes=1000):
        map_id = self.emulator.get_map_id()
        current_x, current_y = self.emulator.get_player_position()
        start_pos = (current_x, current_y)
        target_pos = (target_x, target_y)

        used_memory = False
        path = None
        if use_memory and self._get_collision_tile(target_pos) is None:
            path = self._find_path_in_memory(map_id, start_pos, target_pos, max_nodes=max_nodes)
            used_memory = path is not None

        if path is None:
            path = self.find_path(start_pos, target_pos, max_nodes=max_nodes)

        if path is None:
            return {
                "map_id": map_id,
                "start": start_pos,
                "target": target_pos,
                "path": None,
                "directions": [],
                "length": 0,
                "used_memory": used_memory,
                "error": "no_path_found"
            }

        return {
            "map_id": map_id,
            "start": start_pos,
            "target": target_pos,
            "path": path,
            "directions": self._path_to_directions(start_pos, path),
            "length": len(path),
            "used_memory": used_memory
        }

    def find_path_to_nearest_warp(self, use_memory=True, max_nodes=2000):
        self._refresh_collision_cache()
        map_id = self.emulator.get_map_id()
        current_x, current_y = self.emulator.get_player_position()
        start_pos = (current_x, current_y)

        warps = self.get_known_warps(map_id)
        if not warps:
            return {
                "map_id": map_id,
                "start": start_pos,
                "target": None,
                "path": None,
                "directions": [],
                "length": 0,
                "used_memory": False,
                "error": "no_known_warps"
            }

        warps.sort(key=lambda w: abs(w["pos"][0] - start_pos[0]) + abs(w["pos"][1] - start_pos[1]))

        for warp in warps:
            target_pos = warp["pos"]
            result = self.find_path_to(target_pos[0], target_pos[1], use_memory=use_memory, max_nodes=max_nodes)
            if result.get("path") is not None:
                result["target_warp"] = warp
                return result

        return {
            "map_id": map_id,
            "start": start_pos,
            "target": None,
            "path": None,
            "directions": [],
            "length": 0,
            "used_memory": use_memory,
            "error": "no_reachable_warp"
        }

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

    def visual_guided_step(self, direction: str) -> str:
        """
        Attempts to move in a direction, verifying success via visual and coordinate feedback.
        Returns a descriptive result string.
        """
        if direction not in ["up", "down", "left", "right"]:
            return f"Invalid direction: {direction}"
            
        # 1. Capture Pre-Move State
        start_x, start_y = self.emulator.get_player_position()
        # We use the raw screen image bytes as a simple hash/signature
        start_img = self.emulator.screen_image()
        import hashlib
        start_hash = hashlib.md5(start_img.tobytes()).hexdigest()
        
        # 2. Execute Move (Blindly)
        self.emulator.move_direction(direction)
        
        # 3. Capture Post-Move State
        end_x, end_y = self.emulator.get_player_position()
        end_img = self.emulator.screen_image()
        end_hash = hashlib.md5(end_img.tobytes()).hexdigest()
        
        # 4. Analyze Result
        pos_changed = (start_x != end_x) or (start_y != end_y)
        visual_changed = (start_hash != end_hash)
        
        if pos_changed:
            return f"Moved successfully to ({end_x}, {end_y})"
        elif visual_changed:
            # Position same, but screen changed. 
            # Could be a treadmill, a bump animation, or a warp that kept coords same (rare).
            return "Visual change detected, but position unchanged (Blocked or Treadmill?)"
        else:
            return "Blocked (No visual or position change)"

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
        recent_positions = deque(maxlen=6)
        last_distance = None
        stagnant_steps = 0
        last_debug = None
        
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
            
            # Track progress / oscillation
            recent_positions.append(current_pos)
            if len(recent_positions) >= 4:
                if (recent_positions[-1] == recent_positions[-3] and
                    recent_positions[-2] == recent_positions[-4]):
                    # Oscillation detected, avoid current tile to force re-path
                    # Oscillation detected, avoid current tile to force re-path
                    avoid_set.add(current_pos)
                    last_debug = f"oscillation_detected at {current_pos}, avoiding tile"

                    # OSCILLATION BREAKER: Take a random valid step to break the rhythm
                    # This helps when we are stuck in a logical loop (A -> B -> A)
                    adjacents = self._adjacent_walkable_positions(current_x, current_y)
                    if adjacents:
                         # Pick a random neighbor that isn't the one we just came from (if possible)
                         # adjacents list is [(x, y, dir), ...]
                         random.shuffle(adjacents)
                         for ax, ay, adir in adjacents:
                             # Don't step back into the exact tile we came from if we can avoid it
                             if (ax, ay) == recent_positions[-2]:
                                 continue
                             
                             # Execute the random step
                             btn = DIRECTION_TO_BUTTON.get(adir)
                             if btn:
                                 self.emulator.input(btn, hold_frames=5)
                                 self.emulator.tick(5)
                                 steps_taken += 1
                                 recent_positions.clear() # Reset history
                                 last_debug = f"oscillation_broken: random step {adir}"
                                 break
                    continue

            distance = abs(current_x - path_target[0]) + abs(current_y - path_target[1])
            if last_distance is not None and distance >= last_distance:
                stagnant_steps += 1
            else:
                stagnant_steps = 0
            last_distance = distance
                
            # 2. Pathfind
            # Increased node limit for larger maps or complex paths
            path = self.find_path(current_pos, path_target, known_walls, avoid_set, max_nodes=1000)
            if not path:
                extra = f" debug={last_debug}" if last_debug else ""
                return f"blocked: no path found to ({target_x}, {target_y}) from your current position {current_pos}. Check if you are on an interactive tile (like stairs) and try moving away first.{extra}"
                
            next_step = path[0]
            dx = next_step[0] - current_x
            dy = next_step[1] - current_y

            if stagnant_steps >= 4:
                # Force a different route if we aren't making progress
                known_walls.add(next_step)
                stagnant_steps = 0
                last_debug = f"stagnant_progress at {current_pos}, blocking step {next_step}"
                continue
            
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
            else:
                recent_positions.append(new_pos)
            
            # Periodic tick to keep emulator healthy
            self.emulator.tick(1)
            
        if last_debug:
            return f"max_steps_reached: {last_debug}"
        return "max_steps_reached"
    def interact_with(self, target_x, target_y):
        """
        Interacts with an object at (target_x, target_y).
        Logic: Find adjacent tile -> walk_to it -> Face target -> Press A.
        Returns rich feedback on what happened.
        """
        if self.emulator.is_dialogue_active():
            return "dialogue_active: dialogue or menu is active. Clear the screen before interacting."
        
        # 1. State Tracking: Map current state
        pre_map = self.emulator.get_map_id()
        pre_x, pre_y = self.emulator.get_player_position()
        
        self._refresh_collision_cache()
        
        # 2. Find all adjacent walkable tiles near the target
        adjacents = self._adjacent_walkable_positions(target_x, target_y)
        if not adjacents:
            # Provide diagnostic detail to help tune collision rules.
            neighbor_debug = []
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                pos = (target_x + dx, target_y + dy)
                tile = self._get_collision_tile(pos)
                if tile:
                    neighbor_debug.append(
                        f"{pos}:{tile.get('char')} tid=0x{tile.get('tid'):02X} walkable={tile.get('walkable')}"
                    )
                else:
                    neighbor_debug.append(f"{pos}:unknown (not in cache)")
            return "no_accessible_path: no walkable tile next to target; neighbors=" + ", ".join(neighbor_debug)

        # 3. Sort by distance from player
        adjacents.sort(key=lambda p: abs(p[0]-pre_x) + abs(p[1]-pre_y))

        # 4. Try walking to each
        last_walk_error = None
        for ax, ay, face_dir in adjacents:
            if (pre_x, pre_y) == (ax, ay):
                res = "arrived"
            else:
                res = self.walk_to(ax, ay, max_steps=40)
            
            if res == "arrived":
                # 5. Face target and press A
                btn_map = {
                    "up": BUTTON_UP,
                    "down": BUTTON_DOWN,
                    "left": BUTTON_LEFT,
                    "right": BUTTON_RIGHT
                }
                self.emulator.input(btn_map[face_dir], hold_frames=2)
                self.emulator.tick(2)
                self.emulator.input(BUTTON_A, hold_frames=5)
                self.emulator.tick(10) # Wait for animation/transition
                
                # 6. Analyze Result
                post_map = self.emulator.get_map_id()
                post_x, post_y = self.emulator.get_player_position()
                dialogue_active = self.emulator.is_dialogue_active()
                
                if post_map != pre_map:
                    return f"interaction_success: map_changed to {post_map}"
                if dialogue_active:
                    return "interaction_success: dialogue_started"
                if (post_x != ax or post_y != ay):
                    return f"interaction_success: position_changed to ({post_x}, {post_y})"
                
                # If no state change, check if it's a known step-on warp
                target_tile = self._get_collision_tile((target_x, target_y))
                if target_tile:
                    char = target_tile.get("char")
                    if char in (">", "S"):
                        warp_type = "door" if char == ">" else "stairs"
                        return f"interaction_failed: no state change. This is a {warp_type} (step-on warp). Use walk_to({target_x}, {target_y}) instead of interact_with."
                
                return "interaction_success: but no obvious state change detected."
                
            last_walk_error = res
        
        if last_walk_error:
            return f"no_accessible_path: could not reach a tile adjacent to the target. last_walk={last_walk_error}"
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

    def walk_to_with_path_check(self, target_x, target_y, max_steps=100):
        """
        A robust version of walk_to that intelligently handles unexpected collisions.
        It learns from failed movements and recalculates the path.
        Returns: "arrived", "blocked", "max_steps_reached"
        """
        known_walls = set()
        steps_taken = 0

        while steps_taken < max_steps:
            current_x, current_y = self.emulator.get_player_position()
            current_pos = (current_x, current_y)
            target_pos = (target_x, target_y)

            if current_pos == target_pos:
                return "arrived"

            # Find the next path, avoiding known walls
            self._refresh_collision_cache()
            path = self.find_path(current_pos, target_pos, known_walls=known_walls)

            if not path:
                return f"blocked: no path found to {target_pos} from {current_pos} with known_walls: {known_walls}"

            next_step = path[0]

            # Determine direction and execute move
            direction = self._direction_to_target(current_pos, next_step)
            if direction:
                button = DIRECTION_TO_BUTTON[direction]
                self.emulator.input(button, hold_frames=8) # Slightly longer hold for reliability
                self.emulator.tick(10)
                steps_taken += 1
            else:
                # Should not happen if path is valid
                known_walls.add(next_step)
                continue

            # Verify if the move was successful
            new_pos = self.emulator.get_player_position()
            if new_pos == current_pos:
                # Move failed, the next_step is a wall
                known_walls.add(next_step)

            # Small delay to let the game state settle
            self.emulator.tick(5)

        return "max_steps_reached"
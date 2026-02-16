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

DIRECTION_TO_BITMASK = {
    "up": DIR_UP,
    "down": DIR_DOWN,
    "left": DIR_LEFT,
    "right": DIR_RIGHT
}

class Navigation:
    def __init__(self, emulator: PokemonEmulator, collision_grid, battle_engine=None):
        self.emulator = emulator
        self.battle_engine = battle_engine
        self.collision = collision_grid
        self._world_memory = {}

    def get_map_data(self, radius=6):
        """
        Returns a detailed map grid around the player using definitive collision data.
        """
        return self.collision.get_map_data(radius)

    def _is_tile_walkable(self, pos, from_dir=None):
        """Checks walkability using the definitive collision map data."""
        mask = None
        if from_dir:
            mask = DIRECTION_TO_BITMASK.get(from_dir)
        return self.collision.is_walkable(pos[0], pos[1], from_direction=mask)

    def _adjacent_walkable_positions(self, target_x, target_y):
        adjacents = [
            (target_x, target_y - 1, "down"),
            (target_x, target_y + 1, "up"),
            (target_x - 1, target_y, "right"),
            (target_x + 1, target_y, "left")
        ]
        return [t for t in adjacents if self._is_tile_walkable((t[0], t[1]), from_dir=t[2])]

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

    def find_path(self, start_pos, target_pos, known_walls=None, avoid_positions=None, max_nodes=1000):
        """
        A* pathfinding with a node limit to prevent hangs.
        """
        if start_pos == target_pos:
            return []

        if known_walls is None: known_walls = set()
        if avoid_positions is None: avoid_positions = set()

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
                
            for dx, dy, dname in [(0, 1, "down"), (0, -1, "up"), (1, 0, "right"), (-1, 0, "left")]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Check directional walkability
                is_walkable = self._is_tile_walkable(neighbor, from_dir=dname)
                
                if neighbor in known_walls: continue
                if neighbor in avoid_positions: continue
                if not is_walkable and neighbor != target_pos: continue

                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f = tentative_g_score + self._heuristic(neighbor, target_pos)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))
                    
        return None

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        total_path.reverse()
        return total_path[1:]

    def walk_to(self, target_x, target_y, on_battle="interrupt", avoid_positions=None, max_steps=100):
        """
        Navigate to target coordinates.
        """
        if self.emulator.is_dialogue_active():
             return "stopped: dialogue or menu is active. Clear the screen before walking."

        known_walls = set()
        avoid_set = set(avoid_positions) if avoid_positions else set()
        steps_taken = 0
        recent_positions = deque(maxlen=6)
        stagnant_steps = 0
        last_distance = None
        
        while steps_taken < max_steps:
            current_x, current_y = self.emulator.get_player_position()
            current_pos = (current_x, current_y)
            target_pos = (target_x, target_y)

            if current_pos == target_pos:
                return "arrived"
            
            # Oscillation / Stuck detection
            recent_positions.append(current_pos)
            if len(recent_positions) >= 4:
                if (recent_positions[-1] == recent_positions[-3] and
                    recent_positions[-2] == recent_positions[-4]):
                    avoid_set.add(current_pos)
                    # Random step to break loop
                    adjacents = self._adjacent_walkable_positions(current_x, current_y)
                    if adjacents:
                         random.shuffle(adjacents)
                         for ax, ay, adir in adjacents:
                             if (ax, ay) == recent_positions[-2]: continue
                             btn = DIRECTION_TO_BUTTON.get(adir)
                             if btn:
                                 self.emulator.input(btn, hold_frames=5)
                                 self.emulator.tick(5)
                                 steps_taken += 1
                                 recent_positions.clear()
                                 break
                    continue

            # Pathfinding
            path = self.find_path(current_pos, target_pos, known_walls, avoid_set, max_nodes=1000)
            if not path:
                return f"blocked: no path found to {target_pos} from {current_pos}"
                
            next_step = path[0]
            dx = next_step[0] - current_x
            dy = next_step[1] - current_y

            # Battle Check
            enemy_hp = self.emulator.read_ram(ENEMY_HP_ADDR)
            if enemy_hp > 0:
                if on_battle == "interrupt": return "battle_started"
                # Add run/fight logic if needed
                return "battle_started" # Default to stop for safety

            # Execute Move
            button = None
            if dy == -1: button = BUTTON_UP
            elif dy == 1: button = BUTTON_DOWN
            elif dx == -1: button = BUTTON_LEFT
            elif dx == 1: button = BUTTON_RIGHT
            
            if button:
                self.emulator.input(button, hold_frames=5)
                self.emulator.tick(5)
                steps_taken += 1
                
            # Verify Move
            new_pos = self.emulator.get_player_position()
            if new_pos == current_pos:
                # Blocked?
                known_walls.add(next_step)
                # Retry loop will re-path
            else:
                recent_positions.append(new_pos)
            
        return "max_steps_reached"

    def interact_with(self, target_x, target_y):
        """
        Walks to adjacent tile and presses A towards target.
        """
        if self.emulator.is_dialogue_active():
            return "dialogue_active"
        
        pre_x, pre_y = self.emulator.get_player_position()
        adjacents = self._adjacent_walkable_positions(target_x, target_y)
        if not adjacents:
            return "no_accessible_path"

        adjacents.sort(key=lambda p: abs(p[0]-pre_x) + abs(p[1]-pre_y))

        for ax, ay, face_dir in adjacents:
            if (pre_x, pre_y) != (ax, ay):
                res = self.walk_to(ax, ay, max_steps=40)
                if res != "arrived": continue
            
            # Face target
            btn_map = {"up": BUTTON_UP, "down": BUTTON_DOWN, "left": BUTTON_LEFT, "right": BUTTON_RIGHT}
            self.emulator.input(btn_map[face_dir], hold_frames=5)
            self.emulator.tick(5)
            self.emulator.input(BUTTON_A, hold_frames=5)
            self.emulator.tick(10)
            return "interaction_attempted"
            
        return "interaction_failed"

    def describe_tile(self, x, y, coordinate_type="screen"):
        return self.emulator.describe_tile(x, y)

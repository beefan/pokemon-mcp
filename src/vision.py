from PIL import Image, ImageDraw, ImageFont
import math

class VisionSystem:
    def __init__(self):
        # GameBoy resolution is 160x144
        self.TILE_SIZE = 16 # Pixels
        # 160/16 = 10 tiles wide, 144/16 = 9 tiles tall. 
        # Wait, the previous grid logic was 20x18. 
        # The screen size in PyBoy might be scaled or the grid logic was scanning memory beyond the screen?
        # Standard GB screen is 10x9 tiles (20x18 8x8 tiles).
        # Pokemon generation 1 uses 16x16 macro-tiles (2x2 8x8 tiles).
        # The visible screen is 10 macro-tiles wide and 9 macro-tiles high.
        pass

    def overlay_grid(self, image: Image.Image, player_pos: tuple) -> Image.Image:
        """
        Draws a grid and coordinate labels on the image.
        player_pos: (x, y) global map coordinates of the player.
        """
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Assumption: Image is 160x144 (or scaled equivalent). 
        # We will iterate by 16px blocks (macro tiles).
        
        # Calculate the top-left global coordinate visible on screen
        # Player is centered. In Gen 1, the player is usually at offset (5, 4) or similar on the screen grid?
        # Actually, let's look at how get_local_map worked. 
        # It returned a 20x18 grid. That's using 8x8 tiles? 
        # Memory map says "Player X/Y" and constants.py has TILE_MAP.
        # If we want a visual grid that matches move_direction (1 step = 1 tile), we usually mean 16x16 pixels.
        
        # Let's draw a 16x16 pixel grid.
        step_x = 16
        step_y = 16
        
        # Determine global coordinates of the top-left corner of the screen
        # The player is typically centered.
        # Screen width = 160px = 10 blocks. Player at index 4 or 5?
        # Screen height = 144px = 9 blocks. Player at index 4?
        
        # Let's align with the previous logic: 
        # previous get_local_map scanned x range(20) and y range(18). 
        # That suggests the previous logic was using 8x8 tiles?
        # 20 * 8 = 160. 18 * 8 = 144. Yes, the previous logic scanned 8x8 tiles.
        # BUT, movement usually happens in 16x16 blocks (1 step).
        # So a "Step" is 2x2 8x8 tiles.
        
        # We should draw the grid based on 16x16 movement tiles for the agent's sanity.
        
        # Global Player Coords (px, py) are in "steps" (16x16 tiles).
        # The screen fits 10 x 9 movement tiles.
        
        screen_tiles_x = width // 16
        screen_tiles_y = height // 16
        
        # The player is roughly in the center.
        # Center x index = 4 (0-9 -> 4 is left-center, 5 is right-center).
        # Center y index = 4 (0-8 -> 4 is exact center).
        
        player_screen_x = 4 # roughly
        player_screen_y = 4 # roughly
        
        px, py = player_pos
        
        top_left_gx = px - player_screen_x
        top_left_gy = py - player_screen_y
        
        try:
            # Simple default font
            font = ImageFont.load_default()
        except:
            font = None

        for y in range(0, height, step_y):
            for x in range(0, width, step_x):
                # Draw grid lines
                draw.rectangle([x, y, x + step_x, y + step_y], outline="red", width=1)
                
                # Calculate global coordinate for this cell
                cell_gx = top_left_gx + (x // step_x)
                cell_gy = top_left_gy + (y // step_y)
                
                # Draw text
                # Only draw last digit to save space, or full coords if they fit?
                # 16x16 is very small for text.
                # Maybe just draw the relative offset? or global?
                # Let's try global x,y.
                label = f"{cell_gx},{cell_gy}"
                
                # Check for player position
                if cell_gx == px and cell_gy == py:
                     draw.rectangle([x+2, y+2, x + step_x-2, y + step_y-2], outline="cyan", width=2)
                     label = "YOU"
                
                # Draw label
                # Shadow/Outline for readability
                tx, ty = x + 2, y + 2
                draw.text((tx+1, ty+1), label, fill="black", font=font)
                draw.text((tx, ty), label, fill="white", font=font)

        return image

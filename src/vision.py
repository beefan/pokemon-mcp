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

    def overlay_grid(self, image: Image.Image, player_pos: tuple, scroll: tuple = (0, 0)) -> Image.Image:
        """
        Draws a grid and coordinate labels on the image.
        Uses SCX/SCY to align grid lines with world tiles.
        player_pos: (x, y) global map coordinates of the player.
        scroll: (scx, scy) hardware scroll registers.
        """
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        step_x = 16
        step_y = 16
        scx, scy = scroll

        # Calculate grid offset (how much the background is shifted)
        # SCX increases as we move Right. So the grid should shift Left.
        off_x = -(scx % 16)
        off_y = -(scy % 16)
        
        # Player is centered at roughly (4, 4) in 16x16 tile space
        # NOTE: This assumption fails at map edges.
        player_screen_x = 4 
        player_screen_y = 4
        
        px, py = player_pos
        top_left_gx = px - player_screen_x
        top_left_gy = py - player_screen_y
        
        try:
            # Use default font
            font = ImageFont.load_default()
        except:
            font = None

        # 1. Draw Grid Lines (Aligned to Tiles)
        # We start from off_x and add steps.
        for y in range(off_y, height, step_y):
            for x in range(off_x, width, step_x):
                draw.rectangle([x, y, x + step_x, y + step_y], outline="red", width=1)
                
                # Debug: Draw small dot at intersection?
                # draw.point((x, y), fill="yellow")

        # 2. Draw Axis Labels (Battleship Style)
        # Align labels with the shifted grid columns
        # Top Row (X Coords)
        col_idx = 0
        for x in range(off_x, width, step_x):
            # Which global column is this?
            # It matches the player's relative grid.
            gx = top_left_gx + col_idx
            
            label = str(gx)
            draw.rectangle([x, 0, x + 16, 10], fill=(0, 0, 0, 128)) 
            draw.text((x + 2, 0), label, fill="yellow", font=font)
            col_idx += 1

        # Left Column (Y Coords)
        row_idx = 0
        for y in range(off_y, height, step_y):
            gy = top_left_gy + row_idx
            label = str(gy)
            draw.rectangle([0, y, 16, y + 10], fill=(0, 0, 0, 128))
            draw.text((1, y), label, fill="yellow", font=font)
            row_idx += 1

        # 3. Highlight Player
        # Calculate pixel position of player on screen
        # We use the hardcoded center for now, aligned to the grid.
        # Logic: Player is at Global (px, py).
        # We need to find which Grid Cell corresponds to (px, py).
        # That is the cell where gx == px and gy == py.
        # Screen X = (px - top_left_gx) * 16 + off_x
        # Screen Y = (py - top_left_gy) * 16 + off_y
        
        p_screen_pixel_x = (px - top_left_gx) * 16 + off_x
        p_screen_pixel_y = (py - top_left_gy) * 16 + off_y
        
        draw.rectangle(
            [p_screen_pixel_x, p_screen_pixel_y, p_screen_pixel_x + step_x, p_screen_pixel_y + step_y], 
            outline="cyan", 
            width=3
        )
        # Move 'P' to bottom-right corner to avoid covering face
        draw.text((p_screen_pixel_x + 8, p_screen_pixel_y + 8), "P", fill="cyan", font=font)

        return image

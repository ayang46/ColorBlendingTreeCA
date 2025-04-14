import tkinter as tk
from tkinter import colorchooser
import numpy as np
import random
from collections import deque

# Grid settings
CELL_SIZE = 15
GRID_WIDTH = 60
GRID_HEIGHT = 40

target_color = np.array([255, 255, 255])  # default white
root = tk.Tk()
root.title("Tree-Structured Color Automaton")

canvas = tk.Canvas(root, width=GRID_WIDTH*CELL_SIZE, height=GRID_HEIGHT*CELL_SIZE)
canvas.pack()
info_label = tk.Label(root, text=f"Target: | Current:  | Distance:")
info_label.pack()

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2])) 

def reset_grid():
    global grid, tree_roots, generation
    generation = 0
    grid = np.zeros((GRID_HEIGHT, GRID_WIDTH, 3))
    
    # Create 3-5 random roots at bottom
    tree_roots = []
    for _ in range(random.randint(3, 5)):
        x = random.randint(0, GRID_WIDTH-1)
        color = np.random.randint(0, 256, 3) #generate random RGB
        grid[GRID_HEIGHT-1, x] = color
        tree_roots.append((GRID_HEIGHT-1, x, color))
    
    draw_grid()
    update_info()

def grow_tree():
    global grid, generation

    if grid is None:
        reset_grid()
        return

    # Check ALL cells for target match before growing. must be within +/- 5 tolerance
    if np.any(np.mean(np.abs(grid - target_color), axis=2) < 5):
        matching_cells = np.where(np.mean(np.abs(grid - target_color), axis=2) < 5)
        print(f"Target reached at cells: {list(zip(matching_cells[0], matching_cells[1]))}") #log the mathced color cell (x, y) location
        update_info()
        return

    new_grid = np.copy(grid)
    growth_points = []

    # Find all current tree pixels (non-black)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if np.any(grid[y, x] > 0):
                growth_points.append((y, x, grid[y, x]))

    # Process each growth point
    for y, x, color in growth_points:
        # Randomly select 2-5 directions from all 8
        directions = [(1, 0)]
        if random.random() < 0.3:  # branch out 30% of the time
            all_dirs = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1), (1, 0),   (1, 1)
            ]
            directions = random.sample(all_dirs, k=random.randint(2, 5))

        for dy, dx in directions:
            ny, nx = y + dy, (x + dx) % GRID_WIDTH  # Wrap around horizontally

            if 0 <= ny < GRID_HEIGHT and np.all(new_grid[ny, nx] == 0):
                # Blend with parent and some randomness toward target
                blend_factor = 0.8 + random.random() * 0.2
                new_color = color * blend_factor + target_color * (1 - blend_factor)

                # Add genetic mutation (Gaussian noise)
                mutation = np.random.normal(0, 15, 3)
                new_color = np.clip(new_color + mutation, 0, 255)

                new_grid[ny, nx] = new_color

    grid = new_grid
    generation += 1
    draw_grid()
    update_info()

    # Continue growing (until generation cap)
    if generation < GRID_HEIGHT * 2:
        root.after(100, grow_tree)
def draw_grid():
    canvas.delete("all")
    distance_map = np.mean(np.abs(grid - target_color), axis=2)
    min_distance = np.min(distance_map)
    
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if np.any(grid[y, x] > 0):
                color = grid[y, x]
                current_distance = distance_map[y, x]
                
                # Highlight cells that reached the target
                if current_distance < 5:
                    # Red border for exact matches
                    outline = "black" if current_distance == min_distance else "white"
                    width = 5 if current_distance == min_distance else 2
                else:
                    outline = rgb_to_hex(color)
                    width = 1
                
                canvas.create_rectangle(
                    x*CELL_SIZE, y*CELL_SIZE,
                    (x+1)*CELL_SIZE, (y+1)*CELL_SIZE,
                    fill=rgb_to_hex(color),
                    outline=outline,
                    width=width
                )

    #Debugging info
    if min_distance < 5:
        matching_cells = np.where(distance_map < 5)
        print(f"Cells at target: {list(zip(matching_cells[0], matching_cells[1]))}")
        print(f"Minimum distance: {min_distance:.2f}") #check if caught the cell within the tolerance before printing

def update_info():
    if len(tree_roots) == 0:
        return
    
    # Find the top active pixel in each column
    top_pixels = []
    for x in range(GRID_WIDTH):
        column = grid[:, x]
        active_indices = np.where(np.any(column > 0, axis=1))[0]
        if len(active_indices) > 0:
            top_row = active_indices.min()  # Find highest active row in this column top left is (0,0)
            top_pixels.append(grid[top_row, x])
    
    if len(top_pixels) > 0:
        # Calculate average of all top pixels
        top_pixels = np.array(top_pixels)
        avg_color = top_pixels.mean(axis=0).astype(int)
        distance = np.mean(np.abs(avg_color - target_color))
        
        info_label.config(
            text=f"Target: {tuple(target_color)} | Current: {tuple(avg_color)} | Distance: {distance:.1f}"
        )

def choose_color():
    global target_color
    color_code = colorchooser.askcolor(title="Choose Target Color")
    if color_code[0]:
        target_color = np.array(color_code[0])
        draw_grid()
        update_info()


# UI Controls
tk.Button(root, text="Pick Target Color", command=choose_color).pack()

mode_frame = tk.Frame(root)
mode_frame.pack(pady=10)

tk.Button(mode_frame, text="Tree Growth", command=lambda: [grow_tree()]).pack()

tk.Button(root, text="Reset", command=reset_grid).pack()

reset_grid()
root.mainloop()
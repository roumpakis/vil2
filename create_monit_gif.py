import os
import imageio.v2 as imageio
import re
import cv2
import matplotlib.pyplot as plt

def create_monit_gif(directory):
    """
    Reads all PNG files in the given directory that contain 'MONITxx' in their name,
    sorts them numerically, creates a GIF, saves it, and visualizes it.
    
    Parameters:
    - directory (str): Path to the directory containing PNG files.
    
    Returns:
    - None
    """
    png_files = []
    pattern = re.compile(r"MONIT(\d{2})")
    
    for file in os.listdir(directory):
        match = pattern.search(file)
        if match and file.lower().endswith(".png"):
            png_files.append((int(match.group(1)), os.path.join(directory, file)))
    
    if not png_files:
        print("No MONITxx PNG files found.")
        return
    
    # Sort files by extracted numerical value
    png_files.sort()
    sorted_images = [cv2.imread(file[1]) for file in png_files]
    
    # Create and save GIF
    gif_path = os.path.join(directory, "monit_animation.gif")
    imageio.mimsave(gif_path, sorted_images, duration=0.5)
    print(f"GIF saved at {gif_path}")
    
    # Display the GIF
    fig, ax = plt.subplots()
    ax.axis("off")
    
    def update(frame):
        ax.imshow(cv2.cvtColor(sorted_images[frame], cv2.COLOR_BGR2RGB))
        ax.set_title(f"Disaster Progression ({frame + 1})")
    
    from matplotlib.animation import FuncAnimation
    anim = FuncAnimation(fig, update, frames=len(sorted_images), interval=400, repeat=True)
    plt.show()
    


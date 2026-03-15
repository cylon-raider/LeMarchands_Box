from vpython import canvas, box, vector, color, rate
import pygame
import sys
import os

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

print("--- System Health Check: Markel Occult Technologies ---")

# 1. Test Audio Initialization
print("[1/3] Initializing Pygame Audio...")
try:
    pygame.mixer.init()
    # Attempt to load the theme just to check pathing
    theme_path = resource_path("assets/theme.mp3")
    if os.path.exists(theme_path):
        pygame.mixer.music.load(theme_path)
        print("      SUCCESS: Audio driver and theme file found.")
    else:
        print(f"      WARNING: assets/theme.mp3 not found at {theme_path}")
except Exception as audio_err:
    print(f"      FAILURE: Audio Error: {audio_err}")

# 2. Test 3D Rendering
print("[2/3] Initializing VPython Canvas...")
try:
    scene = canvas(title='Health Check: 3D Renderer', width=400, height=400)
    test_box = box(pos=vector(0,0,0), size=vector(1,1,1), color=color.orange)
    print("      SUCCESS: 3D Canvas opened in your browser.")
except Exception as vpy_err:
    print(f"      FAILURE: 3D Error: {vpy_err}")

# 3. Test Animation Loop
print("[3/3] Starting Animation Loop (Close browser to stop)...")
try:
    count = 0
    while count < 100:
        rate(60)
        test_box.rotate(angle=0.05, axis=vector(0,1,0))
        count += 1
    print("      SUCCESS: Animation loop completed at 60 FPS.")
except Exception as loop_err:
    print(f"      FAILURE: Loop Error: {loop_err}")

print("-----------------------------------------------------")
print("If you see an orange spinning cube and no errors,")
print("your environment is ready for the final build.")
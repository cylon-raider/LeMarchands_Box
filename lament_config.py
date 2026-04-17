import os
import sys
import threading
import socketserver
import http.server
from types import ModuleType
from math import sin
import pygame
import random
import time

# --- VPYTHON BUNDLING BYPASS ---
if getattr(sys, 'frozen', False):
    # 1. Mock the version module to prevent the engine from checking the disk during import
    gs_mock = ModuleType('vpython.gs_version')
    gs_mock.glowscript_version = lambda: "2.1"
    sys.modules['vpython.gs_version'] = gs_mock

    # 2. Set the path where the JS/CSS files will actually be located
    # We use a neutral name to avoid namespace collisions
    os.environ['VPYTHON_LIBRARY_PATH'] = os.path.join(sys._MEIPASS, 'vpy_libs')

# Import only after environment is prepared
from vpython import (
    canvas, box, vector, color, rate,
    local_light, helix, ring, cylinder,
    button, checkbox, vpython,
)

# --- 2. Helper for PyInstaller Portable Pathing & Local Server ---
def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path).replace("\\", "/")

# VPython WebGL has strict CORS policies that block local file paths (file:///).
# We spin up a local server just for the assets directory to stream the textures.
class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

PORT = 8000
httpd = None
for port in range(8000, 8010):
    try:
        httpd = socketserver.TCPServer(("", port), CORSRequestHandler)
        PORT = port
        break
    except OSError:
        continue

# Start the server in a background thread
if httpd:
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

def get_texture_url(filename: str) -> str:
    # URL to the local server, e.g., http://localhost:8000/assets/top_bottom.jpg
    # We append a timestamp to bust the browser cache so fresh edits are visible immediately
    cache_buster = int(time.time())
    return f"http://localhost:{PORT}/assets/{filename}?t={cache_buster}"

# --- 3. Audio Engine Setup ---
pygame.mixer.init()

def load_audio():
    try:
        pygame.mixer.music.load(resource_path("assets/theme.mp3"))
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
        return {
            "click": pygame.mixer.Sound(resource_path("assets/click.wav")),
            "chains": pygame.mixer.Sound(resource_path("assets/chains.wav")),
            "scream": pygame.mixer.Sound(resource_path("assets/scream.wav"))
        }
    except (pygame.error, FileNotFoundError):
        return None

sfx = load_audio()

# Logic for the toggle
def toggle_music(c):
    if c.checked:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()

# --- 4. 3D Scene Setup ---
scene = vpython.canvas(title='The Lament Configuration: Screen-Used Simulator',
                       width=1200, height=800, background=vpython.color.black,
                       userspin=True, userzoom=True)
scene.forward = vpython.vector(-0.5, -0.3, -1) # Angle the initial camera so the 3D aspect and distinct sides are obvious

portal_light = local_light(pos=vpython.vector(0, 0, -4), color=vpython.color.black)
cenobite_light = local_light(pos=vpython.vector(0, 0, 5), color=vpython.color.black)

# The Portal Wall removed for clarity
pass

# --- 5. The Box ---
# Load original textures through the local HTTP server to bypass CORS file blocks
tex_side = get_texture_url("side_circular.jpg")
tex_fb = get_texture_url("front_back_unique.jpg")
tex_tb = get_texture_url("top_bottom.jpg")

class SolidCube:
    def __init__(self):
        self.pos = vpython.vector(0, 0, 0)
        
        # A full 2x2x2 cube
        w = 2.0
        t = 0.04

        self.plates = []
        
        # Front/Back (Normal orientation: wide X, tall Y, thin local Z)
        pf = vpython.box(pos=vpython.vector(0, 0, w/2), size=vpython.vector(w, w, t), texture={'file': tex_fb}, shininess=0.9)
        
        pb = vpython.box(pos=vpython.vector(0, 0, -w/2), size=vpython.vector(w, w, t), texture={'file': tex_fb}, shininess=0.9)
        pb.rotate(angle=vpython.pi, axis=vpython.vector(0, 1, 0))
        
        # Left/Right Side Circular
        t_side = {'file': tex_side, 'turn': -1} 
        
        pr = vpython.box(pos=vpython.vector(w/2, 0, 0), size=vpython.vector(w, w, t), texture=t_side, shininess=0.9)
        pr.rotate(angle=vpython.pi/2, axis=vpython.vector(0, 1, 0))
        
        # Left plate
        t_side_l = {'file': tex_side, 'turn': 1}
        pl = vpython.box(pos=vpython.vector(-w/2, 0, 0), size=vpython.vector(w, w, t), texture=t_side_l, shininess=0.9)
        pl.rotate(angle=-vpython.pi/2, axis=vpython.vector(0, 1, 0))

        # Top/Bottom
        pt = vpython.box(pos=vpython.vector(0, w/2, 0), size=vpython.vector(w, w, t), texture={'file': tex_tb}, shininess=0.9)
        pt.rotate(angle=-vpython.pi/2, axis=vpython.vector(1, 0, 0))
        
        pbo = vpython.box(pos=vpython.vector(0, -w/2, 0), size=vpython.vector(w, w, t), texture={'file': tex_tb}, shininess=0.9)
        pbo.rotate(angle=vpython.pi/2, axis=vpython.vector(1, 0, 0))

        self.plates = [pf, pb, pl, pr, pt, pbo]

# Create the single solid cube
cube = SolidCube()

keys_down = set()

def handle_keydown(evt):
    keys_down.add(evt.key)
    if evt.key in ['q', 'esc']:
        pygame.mixer.quit()
        sys.exit()

def handle_keyup(evt):
    keys_down.discard(evt.key)

scene.bind('keydown', handle_keydown)
scene.bind('keyup', handle_keyup)
print("UI creating now...")
# --- 8. Execution ---
# Attach UI elements to the title area in a consistent way
scene.append_to_title("  ")
music_toggle = checkbox(bind=toggle_music, text="Background Music", checked=True, pos=scene.title_anchor)

# Add custom wtext for the HTML UI arrow controls and zoom controls
instructions_html = """
<script>
window.addEventListener("keydown", function(e) {
    if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].indexOf(e.key) > -1) {
        e.preventDefault();
    }
}, false);
</script>
<div style="display:flex; flex-direction:column; margin-left: 30px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
  <div style="font-size: 15px; font-weight: bold; color: #d97706; margin-bottom: 5px; letter-spacing: 0.5px;">PRESS physical keyboard keys to interact:</div>
  <div style="display:inline-flex; align-items:center; vertical-align:middle; gap:25px; padding-bottom: 5px;">
    
    <!-- Rotate Keys -->
    <div style="display:inline-flex; align-items:center; gap:12px;">
      <div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
        <kbd style="display:inline-block; width:30px; height:30px; line-height:30px; text-align:center; background:#ffffff; border:1px solid #d1d5db; border-bottom: 3px solid #d1d5db; border-radius:5px; font-weight:bold; color:#374151; font-size:16px; cursor:default; user-select:none;">&#8593;</kbd>
        <div style="display:flex; gap:4px;">
          <kbd style="display:inline-block; width:30px; height:30px; line-height:30px; text-align:center; background:#ffffff; border:1px solid #d1d5db; border-bottom: 3px solid #d1d5db; border-radius:5px; font-weight:bold; color:#374151; font-size:16px; cursor:default; user-select:none;">&#8592;</kbd>
          <kbd style="display:inline-block; width:30px; height:30px; line-height:30px; text-align:center; background:#ffffff; border:1px solid #d1d5db; border-bottom: 3px solid #d1d5db; border-radius:5px; font-weight:bold; color:#374151; font-size:16px; cursor:default; user-select:none;">&#8595;</kbd>
          <kbd style="display:inline-block; width:30px; height:30px; line-height:30px; text-align:center; background:#ffffff; border:1px solid #d1d5db; border-bottom: 3px solid #d1d5db; border-radius:5px; font-weight:bold; color:#374151; font-size:16px; cursor:default; user-select:none;">&#8594;</kbd>
        </div>
      </div>
      <div style="color: #4b5563; display:flex; flex-direction:column; line-height:1.2; user-select:none;">
        <span style="font-size: 15px; font-weight: 600; letter-spacing:0.3px;">Rotate</span>
        <span style="font-size:12px; color:#9ca3af;">Hold to spin</span>
      </div>
    </div>

    <!-- Zoom Keys -->
    <div style="display:inline-flex; align-items:center; gap:12px; border-left: 2px solid #e5e7eb; padding-left: 25px;">
      <div style="display:flex; gap:6px;">
        <kbd style="display:inline-block; width:34px; height:34px; line-height:34px; text-align:center; background:#ffffff; border:1px solid #d1d5db; border-bottom: 3px solid #d1d5db; border-radius:5px; font-weight:bold; color:#374151; font-size:22px; cursor:default; user-select:none;">+</kbd>
        <kbd style="display:inline-block; width:34px; height:34px; line-height:34px; text-align:center; background:#ffffff; border:1px solid #d1d5db; border-bottom: 3px solid #d1d5db; border-radius:5px; font-weight:bold; color:#374151; font-size:22px; cursor:default; user-select:none;">-</kbd>
      </div>
      <div style="color: #4b5563; display:flex; flex-direction:column; line-height:1.2; user-select:none;">
        <span style="font-size: 15px; font-weight: 600; letter-spacing:0.3px;">Zoom</span>
        <span style="font-size:12px; color:#9ca3af;">Hold to scale</span>
      </div>
    </div>
  </div>
</div>
"""
vpython.wtext(text=instructions_html, pos=scene.title_anchor)

while True:
    vpython.rate(60)
    
    # Process continuous inputs
    if keys_down:
        # --- Handle rotation ---
        angle_speed = 0.05
        # Compute camera-relative axes for intuitive rotation
        cam_fwd = scene.forward.norm()
        cam_up = scene.up.norm()
        cam_right = vpython.cross(cam_fwd, cam_up).norm()
        
        if 'left' in keys_down or 'ArrowLeft' in keys_down:
            for p in cube.plates:
                p.rotate(angle=angle_speed, axis=cam_up, origin=vpython.vector(0,0,0))
        if 'right' in keys_down or 'ArrowRight' in keys_down:
            for p in cube.plates:
                p.rotate(angle=-angle_speed, axis=cam_up, origin=vpython.vector(0,0,0))
        if 'up' in keys_down or 'ArrowUp' in keys_down:
            for p in cube.plates:
                p.rotate(angle=angle_speed, axis=cam_right, origin=vpython.vector(0,0,0))
        if 'down' in keys_down or 'ArrowDown' in keys_down:
            for p in cube.plates:
                p.rotate(angle=-angle_speed, axis=cam_right, origin=vpython.vector(0,0,0))

        # --- Handle zooming ---
        if '=' in keys_down or '+' in keys_down:
            # Zoom in (decrease range)
            scene.range = scene.range * 0.95
        if '-' in keys_down or '_' in keys_down:
            # Zoom out (increase range)
            scene.range = scene.range * 1.05
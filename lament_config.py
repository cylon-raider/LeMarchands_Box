import os
import sys
from types import ModuleType
from math import sin
import pygame
import random


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

# --- 2. Helper for PyInstaller Portable Pathing ---
def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

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
                       width=1200, height=800, background=vpython.color.black)

portal_light = local_light(pos=vpython.vector(0, 0, -4), color=vpython.color.black)
cenobite_light = local_light(pos=vpython.vector(0, 0, 5), color=vpython.color.black)

# The Portal Wall
glow_lines = []
for x in range(-10, 11, 2):
    for y in range(-8, 9, 2):
        vpython.box(pos=vpython.vector(x, y, -5), length=1.9, height=0.9, width=0.2, color=vpython.vector(0.05, 0.05, 0.05))
        gh = vpython.box(pos=vpython.vector(x, y - 0.5, -5.1), length=2.0, height=0.04, width=0.01, color=vpython.color.black)
        gv = vpython.box(pos=vpython.vector(x - 1.0, y, -5.1), length=0.04, height=1.0, width=0.01, color=vpython.color.black)
        glow_lines.extend([gh, gv])

# --- 5. The Box Segments ---
tex_side = resource_path("assets/side_circular.jpg")
tex_tb = resource_path("assets/top_bottom.jpg")
tex_fb = resource_path("assets/front_back_unique.jpg")
tex_star = resource_path("assets/star_pattern_inner.jpg")
unique_faces = [tex_side, tex_side, tex_tb, tex_tb, tex_fb, tex_fb]

def create_segment(y_pos):
    shell = vpython.box(pos=vpython.vector(0, y_pos, 0), size=vpython.vector(2, 0.66, 2), texture={'file': unique_faces}, shininess=0.9)
    core = vpython.box(pos=vpython.vector(0, y_pos, 0), size=vpython.vector(1.98, 0.65, 1.98), texture=tex_star, visible=False, emissive=True)
    return shell, core

top_s, top_c = create_segment(0.67)
mid_s, mid_c = create_segment(0)
bot_s, bot_c = create_segment(-0.67)
segments = [top_s, top_c, mid_s, mid_c, bot_s, bot_c]

# --- 6. Hooks, Chains, and Blood ---
def make_hook(start_pos):
    chain = helix(pos=start_pos, axis=vpython.vector(0, 0, 0), radius=0.08, thickness=0.04, color=vpython.vector(0.5, 0.5, 0.5), visible=False)
    hook = ring(pos=start_pos, axis=vpython.vector(1, 0, 0), radius=0.2, thickness=0.08, color=vpython.vector(0.7, 0.7, 0.7), visible=False)
    return chain, hook

c_l, h_l = make_hook(vpython.vector(-7, 7, 2))
c_r, h_r = make_hook(vpython.vector(7, 7, 2))
splatter = cylinder(pos=vpython.vector(0, 0, 4.85), axis=vpython.vector(0, 0, 0.1), radius=0, color=vpython.vector(0.4, 0, 0), opacity=0.9, visible=False)

# --- 7. State Machine and Rituals ---
is_open = False

def handle_key(evt):
    if evt.key in ['q', 'esc']:
        pygame.mixer.quit()
        sys.exit()

scene.bind('keydown', handle_key)

def reset_ritual():
    global is_open
    is_open = False
    portal_light.color = cenobite_light.color = scene.background = vpython.color.black
    splatter.visible = False
    splatter.radius = 0
    c_l.visible = h_l.visible = c_r.visible = h_r.visible = False
    top_s.pos = top_c.pos = vpython.vector(0, 0.67, 0)
    bot_s.pos = bot_c.pos = vpython.vector(0, -0.67, 0)
    top_c.visible = mid_c.visible = bot_c.visible = False
    for line in glow_lines:
        line.color = vpython.color.black
        line.emissive = False

def open_the_box(b):
    global is_open
    print("open_the_box called; is_open =", is_open)
    if not is_open:
        b.disabled = True
        if sfx: sfx["click"].play()
        portal_light.color = vpython.vector(1, 0.4, 0)
        for line in glow_lines:
            line.color = vpython.vector(1, 0.3, 0)
            line.emissive = True
        top_c.visible = mid_c.visible = bot_c.visible = True
        for i in range(100):
            vpython.rate(60)
            top_s.pos.x += 0.02
            top_c.pos.x += 0.02
            bot_s.pos.x -= 0.02
            bot_c.pos.x -= 0.02
            for obj in segments:
                obj.rotate(angle=0.015, axis=vpython.vector(0, 1, 0))
            scene.background = vpython.vector(i / 1000, 0, 0)
        if sfx: sfx["chains"].play()
        c_l.visible = h_l.visible = c_r.visible = h_r.visible = True
        t_l, t_r = vpython.vector(-1.5, -1, 4.9), vpython.vector(1.5, -1, 4.9)
        for i in range(25):
            vpython.rate(50)
            h_l.pos += (t_l - h_l.pos) * 0.25
            h_r.pos += (t_r - h_r.pos) * 0.25
            c_l.axis = h_l.pos - c_l.pos
            c_r.axis = h_r.pos - c_r.pos
        if sfx: sfx["scream"].play()
        splatter.visible = True
        for i in range(150):
            vpython.rate(60)
            if i < 30: splatter.radius += 0.3
            jit = lambda: random.uniform(-0.06, 0.06)
            h_l.pos = t_l + vpython.vector(jit(), jit(), 0)
            h_r.pos = t_r + vpython.vector(jit(), jit(), 0)
            c_l.axis = h_l.pos - c_l.pos
            c_r.axis = h_r.pos - c_r.pos
            pulse = abs(sin(i * 0.2))
            cenobite_light.color = vpython.vector(0.2 * pulse, 0.5 * pulse, 1.0 * pulse)
            scene.background = vpython.vector(0.2, 0, 0) if i % 10 < 5 else vpython.vector(0.1, 0, 0.2)
        is_open = True
        b.disabled = False
        b.text = "RESET PORTAL"
    else:
        reset_ritual()
        b.text = "SOLVE THE BOX"
print("UI creating now...")
# --- 8. Execution ---
# Attach UI elements to the title area in a consistent way
scene.append_to_title("  ")
solve_button = button(text="SOLVE THE BOX", bind=open_the_box)
scene.append_to_title("    ")
music_toggle = checkbox(bind=toggle_music, text="Background Music", checked=True)

while True:
    vpython.rate(60)
import os
import sys

# --- VPython Pathing Fix ---
# No more shutil needed. We just need to help the engine find its own home.
if getattr(sys, 'frozen', False):
    # Tell the VPython engine that its 'base' is the root of our bundle
    os.environ['VPYTHON_LIBRARY_PATH'] = os.path.join(sys._MEIPASS, 'vpython', 'vpython_libraries')

from vpython import *
import pygame
import random

# --- 1. Helper for PyInstaller Portable Pathing ---
def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to resource, works for dev and for PyInstaller.
    Using getattr avoids the '_MEIPASS' linting error in PyCharm.
    """
    # Look for the attribute via string to bypass static analysis
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))

    return os.path.join(base_path, relative_path)

# --- 2. Audio Engine Setup ---
pygame.mixer.init()


def load_audio():
    """Loads music and SFX with specific error handling and unique exception naming."""
    try:
        theme_path = resource_path("assets/theme.mp3")
        pygame.mixer.music.load(theme_path)
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)

        click = pygame.mixer.Sound(resource_path("assets/click.wav"))
        chains = pygame.mixer.Sound(resource_path("assets/chains.wav"))
        scream = pygame.mixer.Sound(resource_path("assets/scream.wav"))
        return click, chains, scream
    except (pygame.error, FileNotFoundError) as audio_err:
        print(f"Audio loading failed: {audio_err}")
        return None, None, None


click_sfx, chain_sfx, scream_sfx = load_audio()

# --- 3. 3D Scene Setup ---
scene = canvas(title='The Lament Configuration: Screen-Used Simulator',
               width=1200, height=800, background=color.black)

# Dynamic Lighting
portal_light = local_light(pos=vector(0, 0, -4), color=color.black)
cenobite_light = local_light(pos=vector(0, 0, 5), color=color.black)

# The Portal Wall (Brick Perimeter)
glow_lines = []
for x in range(-10, 11, 2):
    for y in range(-8, 9, 2):
        box(pos=vector(x, y, -5), length=1.9, height=0.9, width=0.2, color=vector(0.05, 0.05, 0.05))
        gh = box(pos=vector(x, y - 0.5, -5.1), length=2.0, height=0.04, width=0.01, color=color.black)
        gv = box(pos=vector(x - 1.0, y, -5.1), length=0.04, height=1.0, width=0.01, color=color.black)
        glow_lines.extend([gh, gv])

# --- 4. The Box Segments (Multi-Texture Mapping) ---
# VPython texture order: [right, left, top, bottom, front, back]
tex_side = resource_path("assets/side_circular.jpg")
tex_tb = resource_path("assets/top_bottom.jpg")
tex_fb = resource_path("assets/front_back_unique.jpg")
tex_star = resource_path("assets/star_pattern_inner.jpg")

unique_faces = [tex_side, tex_side, tex_tb, tex_tb, tex_fb, tex_fb]


def create_segment(y_pos):
    # The outer brass/wood shell
    shell = box(pos=vector(0, y_pos, 0), size=vector(2, 0.66, 2),
                texture={'file': unique_faces}, shininess=0.9)
    # The hidden star-core (slightly smaller to prevent flickering)
    core = box(pos=vector(0, y_pos, 0), size=vector(1.98, 0.65, 1.98),
               texture=tex_star, visible=False, emissive=True)
    return shell, core


top_s, top_c = create_segment(0.67)
mid_s, mid_c = create_segment(0)
bot_s, bot_c = create_segment(-0.67)
segments = [top_s, top_c, mid_s, mid_c, bot_s, bot_c]


# --- 5. Hooks, Chains, and Blood ---
def make_hook(start_pos):
    chain = helix(pos=start_pos, axis=vector(0, 0, 0), radius=0.08, thickness=0.04, color=vector(0.5, 0.5, 0.5),
                  visible=False)
    hook = ring(pos=start_pos, axis=vector(1, 0, 0), radius=0.2, thickness=0.08, color=vector(0.7, 0.7, 0.7),
                visible=False)
    return chain, hook


c_l, h_l = make_hook(vector(-7, 7, 2))
c_r, h_r = make_hook(vector(7, 7, 2))
splatter = cylinder(pos=vector(0, 0, 4.85), axis=vector(0, 0, 0.1), radius=0, color=vector(0.4, 0, 0), opacity=0.9,
                    visible=False)

# --- 6. The Grand Climax Animation ---
is_open = False


def open_the_box(b):
    global is_open
    if not is_open:
        b.text = "RESET PORTAL"
        if click_sfx: click_sfx.play()

        # 1. Glow the Gate
        portal_light.color = vector(1, 0.4, 0)
        for line in glow_lines:
            line.color = vector(1, 0.3, 0)
            line.emissive = True

        # 2. Z-Slide & Texture Reveal
        top_c.visible = mid_c.visible = bot_c.visible = True
        for i in range(100):
            rate(60)
            top_s.pos.x += 0.02
            top_c.pos.x += 0.02
            bot_s.pos.x -= 0.02
            bot_c.pos.x -= 0.02
            for obj in segments:
                obj.rotate(angle=0.015, axis=vector(0, 1, 0))
            scene.background = vector(i / 1000, 0, 0)  # Flesh-red fade

        # 3. Chains Shoot Out
        if chain_sfx: chain_sfx.play()
        c_l.visible = h_l.visible = c_r.visible = h_r.visible = True
        t_l, t_r = vector(-1.5, -1, 4.9), vector(1.5, -1, 4.9)
        for i in range(25):
            rate(50)
            h_l.pos += (t_l - h_l.pos) * 0.25
            h_r.pos += (t_r - h_r.pos) * 0.25
            c_l.axis = h_l.pos - c_l.pos
            c_r.axis = h_r.pos - c_r.pos

        # 4. Impact, Jitter, and Cenobite Pulse
        if scream_sfx: scream_sfx.play()
        splatter.visible = True
        for i in range(150):
            rate(60)
            if i < 30: splatter.radius += 0.3

            # Tension Jitter
            jit = lambda: random.uniform(-0.06, 0.06)
            h_l.pos = t_l + vector(jit(), jit(), 0)
            h_r.pos = t_r + vector(jit(), jit(), 0)
            c_l.axis = h_l.pos - c_l.pos
            c_r.axis = h_r.pos - c_r.pos

            # Cold Blue Strobe
            pulse = abs(sin(i * 0.2))
            cenobite_light.color = vector(0.2 * pulse, 0.5 * pulse, 1.0 * pulse)
            if i % 10 < 5:
                scene.background = vector(0.1, 0, 0.2)
            else:
                scene.background = vector(0.2, 0, 0)
        is_open = True
    else:
        # Reset the scene back to cube
        b.text = "SOLVE THE BOX"
        is_open = False
        # (Reset logic omitted for brevity, simply restart app to replay)


# --- 7. Execution ---
button(text="SOLVE THE BOX", bind=open_the_box, pos=scene.title_anchor)

while True:
    rate(60)
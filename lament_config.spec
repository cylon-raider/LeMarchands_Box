# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# --- IDE Linter Silence (PyCharm/VS Code) ---
try:
    # These imports don't exist in a normal Python env,
    # but defining them here stops the "Unresolved Reference" errors.
    from PyInstaller.building.api import Analysis, PYZ, EXE, COLLECT, BUNDLE
except ImportError:
    pass

# 1. Bytecode & Logic Setup
sys.setrecursionlimit(5000)
block_cipher = None  # Crucial: Must be defined before being used below

# 2. Dependency Paths
# Ensure this matches the path we sniffed out in MINGW64 earlier
VP_LIBS = r'<ABSOLUTE_PATH_TO_VENV_SITE_PACKAGES>\vpython\vpython_libraries'

a = Analysis(
    ['lament_config.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/*', 'assets'),
        # Map the JS/CSS files to a name that NEVER conflicts with a module
        (os.path.join(VP_LIBS, '*'), 'vpy_libs'),
    ],
    hiddenimports=['pkg_resources'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='lament_config',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Toggle to False for the final 'Silent' build
    icon='box_icon.ico',
    version='file_version_info.txt',
)
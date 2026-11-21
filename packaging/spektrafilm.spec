# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the spektrafilm desktop app (one-folder bundle).
# Build from the repository root:  pyinstaller packaging/spektrafilm.spec
import sys
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

with open(Path(SPECPATH).parent / 'pyproject.toml', 'rb') as f:
    VERSION = tomllib.load(f)['project']['version']

datas, binaries, hiddenimports = [], [], []

# Packages that ship data files, native libraries or load submodules
# dynamically (napari plugins, vispy shaders, colour-science datasets, ...).
for package in [
    'spektrafilm',
    'spektrafilm_gui',
    'spektrafilm_lut_creator',
    'napari',
    'napari_builtins',
    'napari_svg',
    'npe2',
    'app_model',
    'magicgui',
    'superqt',
    'vispy',
    'pyconify',
    'colour',
    'OpenImageIO',
    'pyfftw',
    'rawpy',
    'exiv2',
    'lensfunpy',
]:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# npe2 discovers napari plugins through installed distribution metadata.
for dist in ['napari', 'napari-svg', 'npe2', 'app-model', 'magicgui', 'spektrafilm']:
    datas += copy_metadata(dist)

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'tkinter'],
    # numba's cache=True needs the .py sources next to the bytecode.
    module_collection_mode={
        'spektrafilm': 'pyz+py',
        'spektrafilm_gui': 'pyz+py',
        'spektrafilm_lut_creator': 'pyz+py',
    },
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='spektrafilm',
    debug=False,
    strip=False,
    upx=False,
    console=sys.platform == 'linux',
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='spektrafilm',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='spektrafilm.app',
        bundle_identifier='io.github.spektrafilm',
        version=VERSION,
        info_plist={
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': True,
        },
    )

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Imports needed for uvicorn/engineio to work correctly in the frozen executable
needed_imports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.asgi',
    'sqlalchemy.sql.default_comparator',
]

a = Analysis(
    ['src/launcher.py'],           # CHANGED: Point to launcher inside src
    pathex=['src'],                 # CHANGED: Add src to path so imports work
    binaries=[],
    datas=[
        ('src/frontend', 'frontend'), # CHANGED: Source is now src/frontend, Dest stays frontend
    ],
    hiddenimports=needed_imports,
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
    [],
    exclude_binaries=True,
    name='Privemail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,                 # Keep True for debugging, set False for GUI-only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Privemail',
)
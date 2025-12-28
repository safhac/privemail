# privemail_mac.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['apps/privemail/launcher.py'], # Updated path
    pathex=['apps/privemail', '.'], # Added path for the new structure
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('app_data', 'app_data'), 
        # Add any other data folders here
    ],
    hiddenimports=[
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan.on',
        'engineio.async_drivers.asgi',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.ext.baked',
        'sqlite3',
    ],
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
    console=False, # Set to False for a GUI app (hides terminal)
    disable_windowed_traceback=False,
    argv_emulation=True, # Critical for Mac to handle app launch events
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='setup_assets/app_icon.icns' # Uncomment if you have an .icns file
)

# This creates the .app bundle
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

app = BUNDLE(
    coll,
    name='Privemail.app',
    icon=None, # Put path to .icns file here if you have one
    bundle_identifier='com.privemail.app',
)
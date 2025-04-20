# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['KK Dashboard Automator v1.3.1.py'],
    pathex=[],
    binaries=[],
    datas=[('KDA.ico', '.'), ('logo.png', '.'), ('lang.png', '.'), ('stop.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KK Dashboard Automator v1.3.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['KDA.ico'],
)

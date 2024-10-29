# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:/Projects/CCTM/cttm_v110.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\Projects\\CCTM\\rsc', 'rsc')],
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
    [],
    exclude_binaries=True,
    name='CTTM_v110',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['E:\\Projects\\CCTM\\rsc\\CTTM v1.0.0.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CTTM_v110',
)

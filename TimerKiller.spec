# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for TimerKiller

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['c:\\Users\\Yassine Saddiki\\Desktop\\SaaS\\TimerKiller'],
    binaries=[],
    datas=[
        ('app/Media', 'app/Media'),
        ('app/data/state.json', 'app/data'),
    ],
    hiddenimports=['PySide6.QtGui', 'PySide6.QtCore', 'PySide6.QtWidgets', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='TimerKiller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/Media/icon.ico' if False else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TimerKiller',
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('gui', 'gui'), ('core', 'core'), ('config', 'config')],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'core.path_utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6.QtNetwork', 'PyQt6.QtOpenGL', 'PyQt6.QtPrintSupport', 'PyQt6.QtSql', 'PyQt6.QtTest', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets', 'PyQt6.QtPositioning', 'PyQt6.QtSensors', 'PyQt6.QtSerialPort', 'PyQt6.QtWebChannel', 'PyQt6.QtWebSockets', 'PyQt6.QtXml', 'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas', 'PIL.ImageTk', 'PIL.ImageDraw2', 'PIL.ImageCms', 'PIL.ImageFilter', 'PIL.ImageEnhance', 'PIL.ImageOps', 'PIL.ImagePath', 'PIL.ImageSequence', 'PIL.ImageStat', 'PIL.ImageWin'],
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
    name='SurfManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\surfmanager.ico'],
)

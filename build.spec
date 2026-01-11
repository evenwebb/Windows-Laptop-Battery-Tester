# -*- mode: python ; coding: utf-8 -*-
import PyInstaller.utils.hooks as hooks

block_cipher = None

# Collect all psutil submodules and binaries
psutil_datas, psutil_binaries, psutil_hiddenimports = hooks.collect_all('psutil')

# Collect PIL/Pillow data files (fonts, etc.)
pil_datas, pil_binaries, pil_hiddenimports = hooks.collect_all('PIL')

# Collect matplotlib data files and hidden imports
matplotlib_datas, matplotlib_binaries, matplotlib_hiddenimports = hooks.collect_all('matplotlib')

# Combine all binaries and datas
all_binaries = psutil_binaries + pil_binaries + matplotlib_binaries
all_datas = psutil_datas + pil_datas + matplotlib_datas

a = Analysis(
    ['battery_tester.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=[
        'psutil',
        'psutil._psplatform',
        'psutil._pswindows',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL._tkinter_finder',
        'wmi',
        'win32api',
        'win32con',
        'win32com',
        'win32com.client',
        'win32com.shell',
        'pythoncom',
        'pywintypes',
        'matplotlib',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'hardware_info',
        'battery_monitor',
        'battery_health',
        'data_logger',
        'test_validator',
        'test_resumer',
        'power_manager',
        'charging_monitor',
        'low_battery_handler',
        'metadata_logger',
        'backup_manager',
        'results_viewer',
        'report_generator',
    ] + psutil_hiddenimports + pil_hiddenimports + matplotlib_hiddenimports,
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
    name='battery_tester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

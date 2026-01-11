# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['battery_tester.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'psutil',
        'PIL',
        'wmi',
        'win32api',
        'win32con',
        'win32com',
        'matplotlib',
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

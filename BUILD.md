# Build Instructions

This document describes how to build the Windows Battery Tester executable.

## Prerequisites

1. **Python 3.8 or higher** installed on Windows
2. **pip** package manager
3. **Administrator privileges** (recommended for some operations)

## Step 1: Install Dependencies

Install both runtime and development dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Step 2: Test the Script

Before building, test that the script runs correctly:

```bash
python battery_tester.py --validate
```

This will run validation checks without starting a test.

## Step 3: Build with PyInstaller

### Option A: Using the Build Script (Recommended)

Run the provided batch script:

```bash
build.bat
```

This will:
1. Clean previous builds
2. Run PyInstaller with the spec file
3. Copy the executable to the root directory

### Option B: Manual Build

Run PyInstaller directly:

```bash
pyinstaller build.spec
```

The executable will be created in `dist/battery_tester.exe`

## Step 4: Test the Executable

Test the built executable:

```bash
dist\battery_tester.exe --validate
```

## Build Configuration

The `build.spec` file contains the PyInstaller configuration:

- **One-file mode**: Creates a single executable file
- **Hidden imports**: Includes all required modules
- **Icon**: Can be customized (currently uses default)
- **Console mode**: Shows console window (can be changed to windowed mode)

### Customizing the Build

Edit `build.spec` to customize:

- **Icon**: Change `icon='icon.ico'` to use a custom icon
- **Console mode**: Change `console=True` to `console=False` for windowed mode
- **One-file vs One-folder**: Change `a.binaries` and `a.datas` for folder mode

## Distribution

To distribute the application:

1. Copy `battery_tester.exe` to a folder
2. Include `README.md` for user instructions
3. The executable is self-contained - no additional files needed

### Optional Files to Include

- `README.md` - User documentation
- `BUILD.md` - Build instructions (for developers)
- `PLAN.md` - Project plan (for developers)

## Troubleshooting

### PyInstaller Fails

- Ensure all dependencies are installed
- Try running as administrator
- Check that Python is in PATH

### Executable Doesn't Run

- Check Windows Defender/antivirus isn't blocking it
- Try running from command prompt to see error messages
- Ensure all required DLLs are included (PyInstaller should handle this)

### Large Executable Size

The executable includes Python interpreter and all dependencies, so it will be large (50-100MB). This is normal for PyInstaller one-file builds.

To reduce size:
- Use one-folder mode instead of one-file
- Exclude unused modules
- Use UPX compression (advanced)

## Advanced: Creating Installer

To create an installer (optional):

1. Use Inno Setup or NSIS
2. Include the executable
3. Add shortcuts to Start Menu
4. Set up file associations if needed

## Version Information

To add version information to the executable:

1. Create a `version_info.txt` file
2. Use `pyi-grab_version` to extract version from another executable
3. Add version info to `build.spec`

Example `version_info.txt`:
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    ...
  ),
  ...
)
```

Then in `build.spec`:
```python
exe = EXE(
    ...
    version='version_info.txt',
)
```

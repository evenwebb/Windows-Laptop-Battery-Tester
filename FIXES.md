# Build and Runtime Fixes

This document summarizes fixes applied to prevent common import and bundling errors.

## Issues Fixed

### 1. psutil ModuleNotFoundError
**Problem**: PyInstaller wasn't bundling psutil's C extension binaries (.pyd files)

**Solution**: 
- Added `hooks.collect_all('psutil')` to automatically collect all psutil modules, binaries, and data files
- Added psutil submodules to hiddenimports: `psutil._psplatform`, `psutil._pswindows`

**Files Modified**: `build.spec`

### 2. PIL/Pillow Bundling
**Problem**: PIL fonts and image libraries might not be bundled correctly

**Solution**:
- Added `hooks.collect_all('PIL')` to collect all PIL data files and binaries
- Added explicit PIL imports: `PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFont`

**Files Modified**: `build.spec`

### 3. Matplotlib Backend Issues
**Problem**: Matplotlib backend might not be included, causing import errors

**Solution**:
- Added `hooks.collect_all('matplotlib')` to collect matplotlib data files
- Explicitly included backend: `matplotlib.backends.backend_agg`
- Added matplotlib submodules: `matplotlib.figure`, `matplotlib.pyplot`

**Files Modified**: `build.spec`

### 4. pywin32 Modules
**Problem**: Windows API modules might not be bundled correctly

**Solution**:
- Added all pywin32 modules to hiddenimports:
  - `win32api`, `win32con`, `win32com`, `win32com.client`, `win32com.shell`
  - `pythoncom`, `pywintypes`

**Files Modified**: `build.spec`

### 5. Missing Dependencies Setup
**Problem**: Users running Python script directly might not have dependencies installed

**Solution**:
- Created `setup.bat` script to automatically install all dependencies
- Updated `build.bat` to install dependencies before building
- Updated `README.md` with clear installation instructions

**Files Created/Modified**: 
- `setup.bat` (new)
- `build.bat`
- `README.md`

## Build Configuration Summary

The `build.spec` file now:
1. Uses PyInstaller hooks to automatically collect:
   - psutil (all modules, binaries, data)
   - PIL/Pillow (fonts, image libraries)
   - matplotlib (backends, data files)

2. Explicitly includes all hidden imports:
   - All local modules (hardware_info, battery_monitor, etc.)
   - Windows-specific modules (wmi, win32api, etc.)
   - Image processing modules (PIL.*)
   - Plotting modules (matplotlib.*)

3. Combines all binaries and data files from collected packages

## Testing Checklist

Before distributing the executable, test:

- [ ] Run `python battery_tester.py --validate` (should work after `pip install -r requirements.txt`)
- [ ] Build executable: `build.bat`
- [ ] Test executable: `dist\battery_tester.exe --validate`
- [ ] Test on clean Windows machine (without Python installed)
- [ ] Verify all features work:
  - [ ] Battery detection
  - [ ] Hardware info collection
  - [ ] Report generation (JPEG)
  - [ ] Data logging
  - [ ] Power management

## Common Issues and Solutions

### Issue: ModuleNotFoundError when running Python script
**Solution**: Run `setup.bat` or `pip install -r requirements.txt`

### Issue: ModuleNotFoundError in compiled EXE
**Solution**: 
1. Ensure dependencies are installed: `pip install -r requirements.txt`
2. Rebuild: `build.bat`
3. If still failing, check PyInstaller version: `pip install --upgrade pyinstaller`

### Issue: Font loading errors in reports
**Solution**: PIL will fall back to default font. This is handled gracefully in `report_generator.py`

### Issue: WMI access denied
**Solution**: Run as administrator. The code handles WMI failures gracefully.

## Files Modified

1. `build.spec` - Enhanced PyInstaller configuration
2. `build.bat` - Added dependency installation step
3. `setup.bat` - New file for easy dependency installation
4. `README.md` - Updated installation instructions
5. `BUILD.md` - Enhanced troubleshooting section

## Next Steps

If you encounter any new import errors:

1. Check which module is missing
2. Add it to `hiddenimports` in `build.spec`
3. If it's a package with C extensions (like psutil), use `hooks.collect_all('package_name')`
4. Rebuild and test

# Windows Laptop Battery Tester

A portable Python application that monitors laptop battery life, logs data periodically, survives hard shutdowns, displays results, and generates a JPEG report with hardware details.

## Features

- **Portable**: Standalone Windows executable - no Python installation required
- **Resilient**: JSON logging survives hard shutdowns
- **Informative**: Detailed hardware specs and battery statistics
- **Visual**: JPEG report for easy sharing/documentation
- **Smart Logging**: Dual-trigger system (time + percentage)
- **Multi-Laptop Support**: Track and compare battery stats across multiple laptops
- **Sorting & Comparison**: Sort laptops by runtime, discharge rate, or other metrics
- **Current Laptop Tracking**: Automatically identify and highlight the laptop running the test
- **Test Validation**: Pre-test checks ensure battery is 100%, AC disconnected, system ready
- **Resume Capability**: Resume interrupted tests from last logged point
- **Multiple Test Runs**: Track multiple test runs per laptop to monitor battery degradation
- **Power Management**: Set power plan to Performance mode for consistent testing, prevent sleep/hibernate
- **Charging Detection**: Detect and log if charger is plugged in during test
- **Battery Health**: Track design capacity, actual capacity, and health percentage via WMI
- **Test Metadata**: Log OS version, power plan, screen brightness, and other environment details
- **Low Battery Handling**: Detect and handle low battery warnings and system shutdowns
- **Data Backup**: Automatic periodic backups and recovery from corruption
- **Auto-Report Generation**: Automatically generate report when test completes

## Requirements

### For Running the Executable
- Windows 10 or Windows 11
- No Python installation required (if using the built executable)

### For Development/Building
- Python 3.8 or higher
- See `requirements.txt` for runtime dependencies
- See `requirements-dev.txt` for build dependencies

## Installation

### Option 1: Use Pre-built Executable
1. Download the `battery_tester.exe` file
2. Place it in a folder
3. Run `battery_tester.exe`

### Option 2: Run from Source
1. Install Python 3.8+ from [python.org](https://www.python.org/)
2. Install dependencies using one of these methods:

   **Windows (recommended):**
   ```bash
   setup.bat
   ```
   
   **Or manually:**
   ```bash
   pip install -r requirements.txt
   ```
3. Run the script:
   ```bash
   python battery_tester.py
   ```

## Usage

### Basic Usage

Simply run the executable or script:
```bash
battery_tester.exe
```

The script will:
1. Identify your laptop
2. Check for existing test data
3. Validate pre-test conditions (100% battery, AC disconnected)
4. Start monitoring when you unplug the charger
5. Log battery data every 1 minute or every 10% drop
6. Generate a report when the test completes

### Command-Line Options

#### Information & Viewing
- `--list`: Show all tested laptops with summary stats
- `--compare [--sort FIELD]`: Show comparison view (sort by: runtime, discharge_rate, battery_health)
- `--current`: Show only current laptop's detailed results
- `--history [laptop_id]`: Show test history for laptop (or current if omitted)
- `--version`: Show version information

#### Report Generation
- `--report [laptop_id]`: Generate JPEG report for laptop (or current if omitted)
- `--report-comparison`: Generate comparison report for all laptops
- `--auto-open`: Automatically open generated reports

#### Test Control
- `--resume`: Resume interrupted test (skip confirmation prompt)
- `--validate`: Run pre-test validation checks only (don't start test)
- `--notes "text"`: Add notes/comments to test run

#### Configuration
- `--low-battery PERCENT`: Set low battery warning threshold (default: 10%)
- `--backup-interval MINUTES`: Set backup interval in minutes (default: 5)
- `--skip-validation`: Skip pre-test validation (use with caution)
- `--sort FIELD`: Sort comparison by field (runtime/discharge_rate/battery_health)

### Quick Examples

```bash
# Basic usage - start new test
battery_tester.exe

# View all laptops summary
battery_tester.exe --list

# Compare laptops sorted by discharge rate
battery_tester.exe --compare --sort discharge_rate

# Generate and auto-open report
battery_tester.exe --report --auto-open

# Start test with custom settings
battery_tester.exe --low-battery 15 --backup-interval 10 --notes "Extended test"

# Resume interrupted test automatically
battery_tester.exe --resume

# Validate system before starting
battery_tester.exe --validate
```

### Complete CLI Documentation

For detailed command reference, examples, and usage patterns, see **[CLI_USAGE.md](CLI_USAGE.md)**.

## How It Works

1. **Laptop Identification**: Generates unique ID from serial number, model, and CPU
2. **Pre-Test Validation**: Checks battery is 100%, AC disconnected, battery health OK
3. **Power Management**: Sets power plan to High Performance, prevents sleep/hibernate
4. **Battery Monitoring**: Polls every 10 seconds, logs every 1 minute or 10% drop
5. **Charging Detection**: Pauses timer and logs event if charger is plugged in during test
6. **Low Battery Handling**: Detects and logs low battery warnings (configurable threshold)
7. **Data Persistence**: Saves to JSON with configurable periodic backups (default: 5 min)
8. **Report Generation**: Automatically creates JPEG report when test completes
9. **Resume Capability**: Can resume interrupted tests from last logged point
10. **Multi-Laptop Tracking**: Stores and compares results across multiple laptops

## Data Storage

Test data is stored in `battery_test_data.json` in the same directory as the executable.

**Backup System:**
- Backups are stored in the `backups/` directory
- Automatically created every 5 minutes during testing (configurable via `--backup-interval`)
- Keeps last 5 backups automatically
- Automatic recovery from corrupted data files
- Backup files named: `battery_test_data_backup_YYYYMMDD_HHMMSS.json`

**Data Structure:**
- Multi-laptop support with unique laptop IDs
- Multiple test runs per laptop
- Complete test metadata (OS, power plan, hardware info)
- Battery health metrics (design capacity, health %)
- Power events log (charging detected/stopped)
- Low battery events log

## Building the Executable

See `BUILD.md` for detailed build instructions.

Quick build:
```bash
pip install -r requirements-dev.txt
pyinstaller build.spec
```

The executable will be in the `dist/` directory.

## Troubleshooting

### "Battery not detected"
- Ensure your laptop has a battery installed
- Check that battery drivers are installed
- Try running as administrator
- Use `--skip-validation` only if you're certain battery is working

### "Could not set High Performance plan"
- Run as administrator (recommended)
- The script will continue with current power plan
- Test will still run but may not be as consistent

### "WMI access denied"
- Run as administrator
- Check Windows Management Instrumentation service is running
- Some battery details may be unavailable without admin rights

### Test interrupted or laptop shut down
- Run the script again - it will detect incomplete test
- Choose to resume or start new test
- Use `--resume` to automatically resume without prompt
- Data is saved periodically, so minimal data loss

### "Low battery threshold" warnings
- Default threshold is 10% - adjust with `--low-battery PERCENT`
- System may shut down before reaching 0% - this is normal
- Test status will be marked as "low_battery_shutdown"

### Report generation fails
- Ensure Pillow (PIL) is installed
- Check disk space available
- Try generating report manually: `battery_tester.exe --report`

### Data file corruption
- Automatic recovery from backups is attempted
- Check `backups/` directory for recent backups
- Manual recovery: Copy backup file and rename to `battery_test_data.json`

## License

This project is provided as-is for battery testing purposes.

## Documentation

- **[CLI_USAGE.md](CLI_USAGE.md)** - Complete command-line interface reference
- **[BUILD.md](BUILD.md)** - Build instructions for creating executable
- **[PLAN.md](PLAN.md)** - Technical implementation plan and architecture

## Tips & Best Practices

1. **Run validation first**: Use `--validate` to check system readiness before long tests
2. **Frequent backups**: Set `--backup-interval 2` for critical tests to minimize data loss
3. **Add notes**: Use `--notes` to document test conditions and context
4. **Monitor multiple laptops**: Use `--list` and `--compare` to track battery performance across devices
5. **Generate reports**: Use `--report --auto-open` to quickly view results
6. **Resume capability**: Tests automatically save progress - use `--resume` to continue after interruptions

## Support

For issues or questions:
- Check the documentation files (CLI_USAGE.md, BUILD.md)
- Review troubleshooting section above
- Check that you're running as administrator for full functionality

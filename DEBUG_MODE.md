# Debug Mode Documentation

## Overview

Debug mode logs all operations, errors, and important events to a log file. This helps troubleshoot issues and verify the application is running correctly.

## Enabling Debug Mode

### Method 1: Command-Line Argument

Add `--debug` flag when running:

```bash
# Python script
python battery_tester.py --debug

# Or with other arguments
python battery_tester.py --debug --validate
python battery_tester.py --debug --list

# Compiled EXE
battery_tester.exe --debug
battery_tester.exe --debug --validate
```

### Method 2: Interactive Menu

1. Run the application without arguments: `battery_tester.exe`
2. Select option **8. Enable Debug Mode** from the menu
3. Debug mode will be enabled for the current session

## Log File Location

Log files are saved in the `logs/` directory with the format:
```
logs/battery_tester_debug_YYYYMMDD_HHMMSS.log
```

Example: `logs/battery_tester_debug_20240115_143022.log`

The log file path is displayed when debug mode is enabled:
```
[DEBUG] Logging enabled. Log file: C:\path\to\logs\battery_tester_debug_20240115_143022.log
```

## What Gets Logged

Debug mode logs:

### Application Lifecycle
- Application startup and shutdown
- Command-line arguments
- Python version and platform info
- Menu selections and user choices

### Initialization
- Component initialization (DataLogger, BatteryMonitor, etc.)
- Configuration settings (low battery threshold, backup interval)
- Data file loading and validation

### Operations
- Laptop identification
- Hardware and battery info collection
- Test start/resume operations
- Validation checks and results
- Power management operations
- Report generation

### Errors and Warnings
- All exceptions with full tracebacks
- Validation errors and warnings
- Operation failures
- User cancellations

### Test Execution
- Battery status checks
- Test progress updates
- Charging detection events
- Low battery warnings
- Test completion status

## Log Levels

The log file uses standard logging levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

## Example Log Output

```
2024-01-15 14:30:22 [INFO] ======================================================================
2024-01-15 14:30:22 [INFO] DEBUG MODE ENABLED
2024-01-15 14:30:22 [INFO] ======================================================================
2024-01-15 14:30:22 [INFO] Log file: C:\path\to\logs\battery_tester_debug_20240115_143022.log
2024-01-15 14:30:22 [INFO] Python version: 3.11.0
2024-01-15 14:30:22 [INFO] Platform: win32
2024-01-15 14:30:22 [INFO] Command line arguments: ['battery_tester.py', '--debug']
2024-01-15 14:30:22 [INFO] ======================================================================
2024-01-15 14:30:22 [INFO] Application started
2024-01-15 14:30:22 [INFO] Initializing BatteryTester
2024-01-15 14:30:22 [DEBUG] DataLogger initialized. Data file: battery_test_data.json
2024-01-15 14:30:22 [DEBUG] BatteryMonitor initialized
2024-01-15 14:30:22 [INFO] BatteryTester initialization complete
2024-01-15 14:30:22 [INFO] Running in interactive menu mode
2024-01-15 14:30:25 [INFO] User selected menu option: start_test
2024-01-15 14:30:25 [INFO] Identifying laptop...
2024-01-15 14:30:25 [INFO] Generated laptop ID: LAPTOP-ABC123-XPS15-INTEL
2024-01-15 14:30:25 [DEBUG] Hardware info: {'cpu': 'Intel Core i7', ...}
2024-01-15 14:30:25 [INFO] Running validation for laptop: LAPTOP-ABC123-XPS15-INTEL
2024-01-15 14:30:25 [INFO] Validation result - Valid: False, Errors: 1, Warnings: 0
2024-01-15 14:30:25 [ERROR] Validation errors: ['Battery is at 50.0% (should be 100%)']
2024-01-15 14:30:25 [ERROR] Validation failed
```

## Using Logs for Troubleshooting

When reporting issues:

1. **Enable debug mode** before reproducing the issue
2. **Run the operation** that causes the problem
3. **Copy the log file** from the `logs/` directory
4. **Share the log file** - it contains all the information needed to diagnose the issue

### What to Look For

- **ERROR** entries: Indicate what went wrong
- **Exception tracebacks**: Show exactly where and why errors occurred
- **DEBUG** entries: Show detailed state information
- **Timestamps**: Help identify when issues occurred

## Log File Management

- Log files are created with timestamps, so each run creates a new file
- Old log files are not automatically deleted (you can delete them manually)
- Log files can grow large during long test runs - this is normal
- Log files are plain text and can be opened in any text editor

## Tips

1. **Enable debug mode early**: Start with `--debug` to capture everything from the beginning
2. **Check logs after errors**: If something goes wrong, check the most recent log file
3. **Share full logs**: Include the complete log file, not just error lines (context matters)
4. **Log file size**: For very long test runs, logs can be large - this is expected

## Disabling Debug Mode

Debug mode is automatically disabled when the application exits. To disable during a session:

- Exit the application (option 8 or 9 in menu)
- Restart without the `--debug` flag

Note: Once debug mode is enabled via menu, it stays enabled for that session until the application exits.

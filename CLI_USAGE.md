# Command-Line Interface Usage Guide

The Battery Tester provides a comprehensive command-line interface for easy configuration and operation.

## Quick Start

```bash
# Start a new test (interactive mode)
battery_tester.exe

# View all tested laptops
battery_tester.exe --list

# Compare all laptops
battery_tester.exe --compare
```

## Command Reference

### Information & Viewing Commands

#### `--list`
Show all tested laptops with summary statistics.

```bash
battery_tester.exe --list
```

**Output:** Table showing laptop ID, runtime, discharge rate, status, and battery health.

---

#### `--compare [--sort FIELD]`
Show comparison view of all laptops, sorted by specified field.

```bash
# Sort by runtime (default)
battery_tester.exe --compare

# Sort by discharge rate
battery_tester.exe --compare --sort discharge_rate

# Sort by battery health
battery_tester.exe --compare --sort battery_health
```

**Options:**
- `--sort runtime` - Sort by total runtime (default)
- `--sort discharge_rate` - Sort by battery discharge rate
- `--sort battery_health` - Sort by battery health percentage

---

#### `--current`
Show detailed results for the current laptop only.

```bash
battery_tester.exe --current
```

**Output:** Detailed statistics including milestones, hardware info, and test history.

---

#### `--history [LAPTOP_ID]`
Show test history for a specific laptop or current laptop.

```bash
# Show current laptop history
battery_tester.exe --history

# Show specific laptop history
battery_tester.exe --history LAPTOP-ABC123
```

---

### Report Generation Commands

#### `--report [LAPTOP_ID] [--auto-open]`
Generate JPEG report for a laptop.

```bash
# Generate report for current laptop
battery_tester.exe --report

# Generate report for specific laptop
battery_tester.exe --report LAPTOP-ABC123

# Generate and auto-open report
battery_tester.exe --report --auto-open
```

**Options:**
- `--auto-open` - Automatically open the generated report

---

#### `--report-comparison [--auto-open]`
Generate comparison report for all laptops.

```bash
battery_tester.exe --report-comparison

# With auto-open
battery_tester.exe --report-comparison --auto-open
```

---

### Test Control Commands

#### `--resume`
Resume an interrupted test without prompting.

```bash
battery_tester.exe --resume
```

**Use case:** When you know you want to resume and don't want the interactive prompt.

---

#### `--validate`
Run pre-test validation checks only (don't start test).

```bash
battery_tester.exe --validate
```

**Checks:**
- Battery at 100%
- AC power disconnected
- Battery health
- Battery detected

---

#### `--notes "TEXT"`
Add notes/comments to the test run.

```bash
battery_tester.exe --notes "First test after battery replacement"
battery_tester.exe --notes "Testing with WiFi disabled"
```

**Note:** Use quotes if your notes contain spaces.

---

### Configuration Options

#### `--low-battery PERCENT`
Set low battery warning threshold (default: 10%).

```bash
# Warn at 15% instead of 10%
battery_tester.exe --low-battery 15
```

**Range:** 1-20% recommended

---

#### `--backup-interval MINUTES`
Set backup interval in minutes (default: 5).

```bash
# Backup every 10 minutes instead of 5
battery_tester.exe --backup-interval 10

# Backup every minute (for critical tests)
battery_tester.exe --backup-interval 1
```

**Range:** 1-60 minutes recommended

---

#### `--skip-validation`
Skip pre-test validation checks (use with caution).

```bash
battery_tester.exe --skip-validation
```

**Warning:** Only use if you're certain conditions are correct. May result in inaccurate tests.

---

### Utility Commands

#### `--version`
Show version information.

```bash
battery_tester.exe --version
```

---

#### `--help` or `-h`
Show help message with all available options.

```bash
battery_tester.exe --help
battery_tester.exe -h
```

---

## Common Usage Patterns

### Starting a New Test
```bash
# Basic start (with validation)
battery_tester.exe

# Start with custom notes
battery_tester.exe --notes "Production test run"

# Start with custom low battery threshold
battery_tester.exe --low-battery 15
```

### Viewing Results
```bash
# Quick summary
battery_tester.exe --list

# Detailed comparison
battery_tester.exe --compare --sort runtime

# Current laptop details
battery_tester.exe --current
```

### Generating Reports
```bash
# Current laptop report
battery_tester.exe --report

# Specific laptop report (auto-open)
battery_tester.exe --report LAPTOP-ABC123 --auto-open

# Comparison report
battery_tester.exe --report-comparison
```

### Resuming Tests
```bash
# Interactive resume (prompts for confirmation)
battery_tester.exe

# Automatic resume (no prompt)
battery_tester.exe --resume
```

### Advanced Configuration
```bash
# Custom backup interval and low battery threshold
battery_tester.exe --backup-interval 3 --low-battery 12

# Skip validation (for testing/debugging)
battery_tester.exe --skip-validation --notes "Debug test"
```

## Combining Options

You can combine multiple options:

```bash
# Generate report with auto-open for specific laptop
battery_tester.exe --report LAPTOP-ABC123 --auto-open

# Compare sorted by discharge rate
battery_tester.exe --compare --sort discharge_rate

# Start test with custom settings
battery_tester.exe --low-battery 15 --backup-interval 10 --notes "Extended test"
```

## Exit Codes

- `0` - Success
- `1` - Error (validation failed, file error, etc.)

## Tips

1. **Use `--validate` first** to check if your system is ready before starting a long test
2. **Set `--backup-interval` lower** (1-2 minutes) for critical tests to minimize data loss
3. **Use `--auto-open`** with reports to quickly view results
4. **Combine `--resume` with `--notes`** to add context when resuming: `--resume --notes "Resumed after power outage"`
5. **Use `--list` or `--compare`** regularly to track multiple laptops

## Examples

### Example 1: Quick Test Setup
```bash
# Check system readiness
battery_tester.exe --validate

# Start test with notes
battery_tester.exe --notes "Quick test - 30 min expected"
```

### Example 2: Production Testing
```bash
# Start with frequent backups
battery_tester.exe --backup-interval 2 --low-battery 15 --notes "Production test batch 1"
```

### Example 3: Multi-Laptop Comparison
```bash
# View all laptops
battery_tester.exe --list

# Generate comparison report
battery_tester.exe --report-comparison --auto-open
```

### Example 4: Resuming After Interruption
```bash
# Resume automatically
battery_tester.exe --resume --notes "Resumed after system update"
```

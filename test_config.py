"""
Test Configuration Module
Persists preferences to battery_tester.json
"""
import json
import os

DEFAULTS = {
    "low_battery_threshold": 10,
    "backup_interval": 5,
    "default_power_plan": "high_performance",
    "sort_order": "runtime",
    "auto_open_report": False,
    "log_interval_seconds": 10,
    "preset": "full_discharge",
    "csv_export": False,
    "brightness_percent": 100,
    "notes": "",
}


class TestConfig:
    """Persistent test configuration backed by a JSON file."""

    def __init__(self, config_file="battery_tester.json"):
        self.config_file = config_file
        self.data = dict(DEFAULTS)
        self._load()

    def _load(self):
        if not os.path.exists(self.config_file):
            return
        try:
            with open(self.config_file, encoding="utf-8") as f:
                loaded = json.load(f)
            for k, v in loaded.items():
                if k in DEFAULTS:
                    self.data[k] = v
        except (json.JSONDecodeError, OSError, IOError):
            pass

    def save(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Warning: Could not save config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        if key not in DEFAULTS:
            print(f"Warning: Unknown config key '{key}'. Available: {', '.join(DEFAULTS.keys())}")
            return False
        self.data[key] = value
        self.save()
        return True

    def show(self):
        print("\nConfiguration:")
        for k, v in self.data.items():
            print(f"  {k}: {v}")


# --- Test preset definitions (#12) ---
PRESETS = {
    "full_discharge": {
        "name": "Full Discharge",
        "description": "Run battery from 100% to shutdown. Most accurate runtime estimate.",
        "require_100_percent": True,
        "low_battery_threshold": 5,
        "log_interval_seconds": 10,
    },
    "quick_test": {
        "name": "Quick Test",
        "description": "Run for 30 minutes and estimate full runtime from discharge rate.",
        "require_100_percent": False,
        "low_battery_threshold": 50,
        "log_interval_seconds": 5,
        "max_duration_minutes": 30,
    },
    "battery_calibration": {
        "name": "Battery Calibration",
        "description": "Full charge, full discharge, full charge. Helps recalibrate the battery meter.",
        "require_100_percent": True,
        "low_battery_threshold": 0,
        "log_interval_seconds": 10,
        "recharge_after": True,
    },
    "idle_test": {
        "name": "Idle Test",
        "description": "Minimal CPU usage. Measures best-case battery life with screen on.",
        "require_100_percent": False,
        "low_battery_threshold": 5,
        "log_interval_seconds": 30,
        "power_plan": "power_saver",
    },
}

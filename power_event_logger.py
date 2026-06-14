"""
System Power Event Logger
Polls Windows Event Log or WMI for system power transitions.
"""
import platform

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


class PowerEventLogger:
    """Logs system power events (sleep, resume, AC connect/disconnect)."""

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self._wmi = None
        self._last_ac_state = None
        if self.is_windows and WMI_AVAILABLE:
            try:
                self._wmi = wmi.WMI()
            except Exception:
                self._wmi = None

    def poll(self):
        """
        Poll for power events. Returns dict with event info or None.
        Keys: event (ac_connected, ac_disconnected, battery_change), battery_percent
        """
        if not self._wmi:
            return None

        try:
            batteries = self._wmi.Win32_Battery()
            if not batteries:
                return None
            bat = batteries[0]

            pct = getattr(bat, "EstimatedChargeRemaining", None)
            status = getattr(bat, "BatteryStatus", None)
            ac_connected = status in (2, 6, 7) if status is not None else None

            if ac_connected is not None and ac_connected != self._last_ac_state:
                self._last_ac_state = ac_connected
                return {
                    "event": "ac_connected" if ac_connected else "ac_disconnected",
                    "battery_percent": pct,
                }
        except Exception:
            pass

        return None

    def get_power_source(self):
        """Return 'ac' or 'battery' based on current state."""
        if not self._wmi:
            return None
        try:
            batteries = self._wmi.Win32_Battery()
            if batteries:
                status = getattr(batteries[0], "BatteryStatus", None)
                if status in (2, 6, 7):
                    return "ac"
                return "battery"
        except Exception:
            pass
        return None

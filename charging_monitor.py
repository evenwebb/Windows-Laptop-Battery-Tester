"""
Charging Detection Module
Monitors AC power connection during test with a grace period for accidental reconnects.
"""
import time
from datetime import datetime

try:
    from battery_monitor import BatteryMonitor
except ImportError:
    BatteryMonitor = None


class ChargingMonitor:
    """Monitor for charging events during battery test.

    Includes a configurable grace period: if the charger is reconnected briefly
    (e.g. bumped loose), the test won't pause unless it stays connected for the
    full grace period.
    """

    def __init__(self, grace_period=30):
        if BatteryMonitor is None:
            raise ImportError("BatteryMonitor not available")
        self.battery_monitor = BatteryMonitor()
        self.charging_events = []
        self.is_paused = False
        self.pause_start_time = None
        self.total_charging_time = 0
        self.grace_period = grace_period
        self._grace_start = None          # When charging was first detected
        self._grace_warning_shown = False

    def check_charging_status(self):
        """Check if charger is currently connected."""
        status = self.battery_monitor.get_battery_status()
        return status['ac_connected'] or status['charging']

    def update(self):
        """
        Poll charging state with grace period.
        Returns one of: 'ok', 'grace', 'paused', 'resumed', 'charging', None
        """
        charging = self.check_charging_status()

        # Already paused — check if still charging
        if self.is_paused:
            if not charging:
                return self._handle_charging_stopped()
            return 'paused'

        # Not paused, no charging detected — all good
        if not charging:
            self._grace_start = None
            self._grace_warning_shown = False
            return 'ok'

        # Charging detected — start or continue grace period
        now = time.time()
        if self._grace_start is None:
            self._grace_start = now
            self._grace_warning_shown = False
            return 'grace'

        elapsed = now - self._grace_start
        if elapsed < self.grace_period:
            remaining = int(self.grace_period - elapsed)
            if not self._grace_warning_shown and remaining <= 10:
                self._grace_warning_shown = True
            return 'grace'

        # Grace period expired — pause the test
        return self._handle_charging_detected()

    def _handle_charging_detected(self):
        self.is_paused = True
        self.pause_start_time = time.time()
        self._grace_start = None
        self._grace_warning_shown = False

        status = self.battery_monitor.get_battery_status()
        event = {
            'timestamp': datetime.now().isoformat(),
            'event': 'charging_detected',
            'ac_connected': True,
            'battery_percent': status['percentage'],
        }
        self.charging_events.append(event)
        return 'paused'

    def _handle_charging_stopped(self):
        if self.is_paused:
            pause_duration = time.time() - self.pause_start_time
            self.total_charging_time += pause_duration

            status = self.battery_monitor.get_battery_status()
            event = {
                'timestamp': datetime.now().isoformat(),
                'event': 'charging_stopped',
                'ac_connected': False,
                'pause_duration_seconds': pause_duration,
                'battery_percent': status['percentage'],
            }
            self.charging_events.append(event)

        self.is_paused = False
        self.pause_start_time = None
        self._grace_start = None
        return 'resumed'

    @property
    def grace_remaining(self):
        """Seconds remaining in grace period, or 0."""
        if self._grace_start is None or self.is_paused:
            return 0
        elapsed = time.time() - self._grace_start
        return max(0, int(self.grace_period - elapsed))

    def get_total_charging_time(self):
        return self.total_charging_time

    # --- threaded monitor (alternative API, used by __main__ test block) ---
    def monitor(self, stop_event=None):
        last_charging_state = False
        while True:
            if stop_event and stop_event.is_set():
                break
            current_charging = self.check_charging_status()
            if current_charging and not last_charging_state:
                self._handle_charging_detected()
            elif not current_charging and last_charging_state:
                self._handle_charging_stopped()
            last_charging_state = current_charging
            time.sleep(5)
        return self.charging_events


if __name__ == '__main__':
    monitor = ChargingMonitor(grace_period=10)
    print("Charging Monitor Test (10s grace):")
    print("=" * 50)
    import threading
    stop_event = threading.Event()
    thread = threading.Thread(target=monitor.monitor, args=(stop_event,), daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        stop_event.set()
        thread.join(timeout=2)
        print("\n\nCharging Events:")
        for event in monitor.charging_events:
            print(event)
        print(f"\nTotal charging time: {monitor.get_total_charging_time() / 60:.1f} minutes")

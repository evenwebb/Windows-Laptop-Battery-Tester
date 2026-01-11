"""
Charging Detection Module
Monitors AC power connection during test
"""
import time

try:
    from battery_monitor import BatteryMonitor
except ImportError:
    # Handle case when run as standalone
    BatteryMonitor = None


class ChargingMonitor:
    """Monitor for charging events during battery test"""
    
    def __init__(self):
        if BatteryMonitor is None:
            raise ImportError("BatteryMonitor not available")
        self.battery_monitor = BatteryMonitor()
        self.charging_events = []
        self.is_paused = False
        self.pause_start_time = None
        self.total_charging_time = 0
    
    def check_charging_status(self):
        """Check if charger is currently connected"""
        status = self.battery_monitor.get_battery_status()
        return status['ac_connected'] or status['charging']
    
    def handle_charging_detected(self):
        """
        Handle charging detection event
        Returns event dict
        """
        from datetime import datetime
        
        if not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.time()
            
            event = {
                'timestamp': datetime.now().isoformat(),
                'event': 'charging_detected',
                'ac_connected': True,
                'battery_percent': self.battery_monitor.get_battery_status()['percentage'],
            }
            
            self.charging_events.append(event)
            print(f"\n⚠️  WARNING: Charger detected! Test paused.")
            print(f"Battery: {event['battery_percent']:.1f}%")
            print("Please disconnect charger to continue test.")
            
            return event
        
        return None
    
    def handle_charging_stopped(self):
        """
        Handle charging stopped event
        Returns event dict
        """
        from datetime import datetime
        
        if self.is_paused:
            pause_duration = time.time() - self.pause_start_time
            self.total_charging_time += pause_duration
            self.is_paused = False
            
            event = {
                'timestamp': datetime.now().isoformat(),
                'event': 'charging_stopped',
                'ac_connected': False,
                'pause_duration_seconds': pause_duration,
                'battery_percent': self.battery_monitor.get_battery_status()['percentage'],
            }
            
            self.charging_events.append(event)
            print(f"\n✓ Charger disconnected. Test resumed.")
            print(f"Paused for: {pause_duration / 60:.1f} minutes")
            
            return event
        
        return None
    
    def monitor(self, stop_event=None):
        """
        Continuously monitor for charging events
        Returns list of charging events
        """
        last_charging_state = False
        
        while True:
            if stop_event and stop_event.is_set():
                break
            
            current_charging = self.check_charging_status()
            
            # Detect charging start
            if current_charging and not last_charging_state:
                self.handle_charging_detected()
            
            # Detect charging stop
            elif not current_charging and last_charging_state:
                self.handle_charging_stopped()
            
            last_charging_state = current_charging
            time.sleep(5)  # Check every 5 seconds
        
        return self.charging_events
    
    def get_total_charging_time(self):
        """Get total time spent charging during test (in seconds)"""
        return self.total_charging_time


if __name__ == '__main__':
    monitor = ChargingMonitor()
    print("Charging Monitor Test:")
    print("=" * 50)
    print("Monitoring for charging events...")
    print("Press Ctrl+C to stop")
    
    try:
        import threading
        stop_event = threading.Event()
        thread = threading.Thread(target=monitor.monitor, args=(stop_event,))
        thread.start()
        thread.join()
    except KeyboardInterrupt:
        stop_event.set()
        print("\n\nCharging Events:")
        for event in monitor.charging_events:
            print(event)
        print(f"\nTotal charging time: {monitor.get_total_charging_time() / 60:.1f} minutes")

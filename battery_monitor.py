"""
Battery Monitoring Module
Monitors battery status, percentage, and charging state
"""
import time
import platform
import psutil

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


class BatteryMonitor:
    """Monitor battery status and detect power source changes"""
    
    def __init__(self):
        self.last_percentage = None
        self.last_charging_state = None
        self.poll_interval = 10  # seconds
        
    def get_battery_status(self):
        """
        Get current battery status
        Returns dict with: percentage, charging, ac_connected, design_capacity, full_charge_capacity
        """
        status = {
            'percentage': None,
            'charging': False,
            'ac_connected': False,
            'design_capacity_mwh': None,
            'full_charge_capacity_mwh': None,
        }
        
        # Use psutil for basic battery info
        try:
            battery = psutil.sensors_battery()
            if battery:
                status['percentage'] = round(battery.percent, 2)
                status['charging'] = battery.power_plugged
                status['ac_connected'] = battery.power_plugged
        except Exception as e:
            print(f"Warning: Could not get battery status from psutil: {e}")
        
        # Use WMI for detailed battery info (Windows)
        if WMI_AVAILABLE and platform.system() == 'Windows':
            try:
                c = wmi.WMI()
                batteries = c.Win32_Battery()
                
                if batteries:
                    battery = batteries[0]
                    
                    # Get percentage from WMI if available
                    if battery.EstimatedChargeRemaining is not None:
                        status['percentage'] = battery.EstimatedChargeRemaining
                    
                    # Get charging status
                    # BatteryStatus: 2 = Charging, 1 = Discharging, 3 = AC Power
                    if battery.BatteryStatus == 2:
                        status['charging'] = True
                    elif battery.BatteryStatus == 1:
                        status['charging'] = False
                    
                    # Check AC power via Win32_Battery
                    # When AC is connected, battery may still show as discharging briefly
                    # So we check both BatteryStatus and power_plugged
                    if battery.BatteryStatus == 3 or battery.BatteryStatus == 2:
                        status['ac_connected'] = True
                    
                    # Get capacity info
                    if battery.DesignCapacity:
                        status['design_capacity_mwh'] = battery.DesignCapacity
                    if battery.FullChargeCapacity:
                        status['full_charge_capacity_mwh'] = battery.FullChargeCapacity
                        
            except Exception as e:
                print(f"Warning: Could not get battery status from WMI: {e}")
        
        return status
    
    def is_on_battery(self):
        """Check if laptop is running on battery (AC disconnected)"""
        status = self.get_battery_status()
        return not status['ac_connected'] and not status['charging']
    
    def wait_for_battery_power(self):
        """
        Wait until laptop switches to battery power
        Returns True when on battery, False if interrupted
        """
        print("Waiting for AC power to be disconnected...")
        print("Please unplug the charger.")
        
        while True:
            if self.is_on_battery():
                print("✓ Running on battery power")
                return True
            
            status = self.get_battery_status()
            if status['percentage']:
                print(f"Battery: {status['percentage']:.1f}% | AC Connected: {status['ac_connected']}", end='\r')
            
            time.sleep(self.poll_interval)
    
    def monitor_battery(self, callback=None, stop_event=None):
        """
        Continuously monitor battery status
        callback: function(status_dict) called on each poll
        stop_event: threading.Event to stop monitoring
        """
        while True:
            if stop_event and stop_event.is_set():
                break
            
            status = self.get_battery_status()
            
            # Check for charging during test
            if status['ac_connected'] or status['charging']:
                if self.last_charging_state == False:  # Was on battery, now charging
                    if callback:
                        callback({'event': 'charging_detected', **status})
            
            # Check for percentage drops (10% increments)
            if self.last_percentage is not None and status['percentage'] is not None:
                current_10pct = int(status['percentage'] / 10)
                last_10pct = int(self.last_percentage / 10)
                
                if current_10pct < last_10pct:
                    if callback:
                        callback({'event': 'percentage_drop', **status})
            
            # Update last known state
            self.last_percentage = status['percentage']
            self.last_charging_state = status['charging']
            
            if callback:
                callback({'event': 'status_update', **status})
            
            time.sleep(self.poll_interval)


if __name__ == '__main__':
    monitor = BatteryMonitor()
    print("Battery Status:")
    print("=" * 50)
    status = monitor.get_battery_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    print(f"\nIs on battery: {monitor.is_on_battery()}")

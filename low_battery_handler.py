"""
Low Battery Handler Module
Detects and handles low battery warnings
"""
from datetime import datetime


class LowBatteryHandler:
    """Handle low battery warnings and shutdown scenarios"""
    
    def __init__(self, low_battery_threshold=10):
        self.low_battery_threshold = low_battery_threshold
        self.low_battery_events = []
        self.low_battery_warning_shown = False
    
    def check_low_battery(self, battery_percent):
        """
        Check if battery is at low level
        Returns (is_low, event_dict)
        """
        if battery_percent is None:
            return False, None
        
        if battery_percent <= self.low_battery_threshold and not self.low_battery_warning_shown:
            self.low_battery_warning_shown = True
            
            event = {
                'timestamp': datetime.now().isoformat(),
                'battery_percent': battery_percent,
                'event': 'low_battery_warning',
            }
            
            self.low_battery_events.append(event)
            
            print(f"\n⚠️  LOW BATTERY WARNING: {battery_percent:.1f}%")
            print("System may shut down soon. Test will continue until shutdown.")
            
            return True, event
        
        return False, None
    
    def determine_test_status(self, last_battery_percent, last_entry_time):
        """
        Determine test status based on final state
        Returns status string: "completed", "low_battery_shutdown", "hard_shutdown"
        """
        if last_battery_percent is None:
            return "hard_shutdown"
        
        if last_battery_percent <= 0:
            return "completed"
        elif last_battery_percent <= self.low_battery_threshold:
            return "low_battery_shutdown"
        else:
            return "hard_shutdown"
    
    def get_low_battery_events(self):
        """Get all low battery events"""
        return self.low_battery_events


if __name__ == '__main__':
    handler = LowBatteryHandler()
    
    # Simulate battery levels
    test_levels = [25, 15, 10, 8, 5, 2, 0]
    
    print("Low Battery Handler Test:")
    print("=" * 50)
    for level in test_levels:
        is_low, event = handler.check_low_battery(level)
        if is_low:
            print(f"Event: {event}")
    
    print(f"\nTest Status: {handler.determine_test_status(0, None)}")
    print(f"\nLow Battery Events: {len(handler.get_low_battery_events())}")

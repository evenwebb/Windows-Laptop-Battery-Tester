"""
Test Validation Module
Pre-test validation checks
"""
try:
    from battery_monitor import BatteryMonitor
    from battery_health import get_battery_health, check_battery_health_threshold
    from data_logger import DataLogger
except ImportError:
    # Handle case when run as standalone
    BatteryMonitor = None
    get_battery_health = None
    check_battery_health_threshold = None
    DataLogger = None


class TestValidator:
    """Validate test conditions before starting"""
    
    def __init__(self):
        if BatteryMonitor is None:
            raise ImportError("BatteryMonitor not available")
        self.battery_monitor = BatteryMonitor()
        self.errors = []
        self.warnings = []
    
    def validate_battery_charge(self, threshold=100):
        """Verify battery is at specified charge level"""
        status = self.battery_monitor.get_battery_status()
        
        if status['percentage'] is None:
            self.errors.append("Battery not detected by system")
            return False
        
        if status['percentage'] < threshold:
            self.warnings.append(
                f"Battery is at {status['percentage']:.1f}% (should be {threshold}%)"
            )
            return False
        
        return True
    
    def validate_ac_disconnected(self):
        """Verify AC power is disconnected"""
        status = self.battery_monitor.get_battery_status()
        
        if status['ac_connected'] or status['charging']:
            self.errors.append("AC power is still connected. Please disconnect charger.")
            return False
        
        return True
    
    def validate_battery_health(self, threshold=80):
        """Check battery health"""
        if get_battery_health is None:
            self.warnings.append("Could not retrieve battery health information")
            return True  # Not a blocking error
        
        health_info = get_battery_health()
        
        if health_info is None:
            self.warnings.append("Could not retrieve battery health information")
            return True  # Not a blocking error
        
        if check_battery_health_threshold is None:
            return True
        
        is_low, warning = check_battery_health_threshold(health_info, threshold)
        if is_low:
            self.warnings.append(warning)
            return True  # Warning but not blocking
        
        return True
    
    def validate_battery_detected(self):
        """Verify battery is detected by system"""
        status = self.battery_monitor.get_battery_status()
        
        if status['percentage'] is None:
            self.errors.append("Battery not detected by system")
            return False
        
        return True
    
    def check_incomplete_test(self, laptop_id, data_logger):
        """Check if there's an incomplete test for this laptop"""
        test_run = data_logger.get_current_test_run(laptop_id)
        
        if test_run:
            self.warnings.append(
                f"Incomplete test found (started: {test_run['test_start_time']}). "
                "You can resume or start a new test."
            )
            return True
        
        return False
    
    def validate_all(self, laptop_id=None, data_logger=None, require_100_percent=True):
        """
        Run all validation checks
        Returns (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Check battery detected
        if not self.validate_battery_detected():
            return False, self.errors, self.warnings
        
        # Check battery charge
        if require_100_percent:
            if not self.validate_battery_charge(100):
                return False, self.errors, self.warnings
        
        # Check AC disconnected
        if not self.validate_ac_disconnected():
            return False, self.errors, self.warnings
        
        # Check battery health (warning only)
        self.validate_battery_health()
        
        # Check for incomplete tests
        if laptop_id and data_logger:
            self.check_incomplete_test(laptop_id, data_logger)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def display_results(self):
        """Display validation results"""
        if self.errors:
            print("\n❌ Validation Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  Validation Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✓ All validation checks passed!")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    validator = TestValidator()
    
    print("Test Validation:")
    print("=" * 50)
    
    is_valid, errors, warnings = validator.validate_all()
    validator.display_results()
    
    if is_valid:
        print("\nReady to start test!")
    else:
        print("\nPlease fix errors before starting test.")

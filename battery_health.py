"""
Battery Health Monitor Module
Retrieves battery health metrics via WMI
"""
import platform

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


def get_battery_health():
    """
    Retrieve battery health metrics via WMI (Win32_Battery)
    Returns dict with battery health info or None if unavailable
    """
    if not WMI_AVAILABLE or platform.system() != 'Windows':
        return None
    
    try:
        c = wmi.WMI()
        batteries = c.Win32_Battery()
        
        if not batteries:
            return None
        
        battery = batteries[0]
        
        health_info = {
            'design_capacity_mwh': None,
            'full_charge_capacity_mwh': None,
            'health_percent': None,
            'cycles': None,
        }
        
        # Design Capacity (mWh)
        if battery.DesignCapacity:
            health_info['design_capacity_mwh'] = battery.DesignCapacity
        
        # Full Charge Capacity (mWh)
        if battery.FullChargeCapacity:
            health_info['full_charge_capacity_mwh'] = battery.FullChargeCapacity
        
        # Calculate Health Percentage
        if health_info['design_capacity_mwh'] and health_info['full_charge_capacity_mwh']:
            health_info['health_percent'] = round(
                (health_info['full_charge_capacity_mwh'] / health_info['design_capacity_mwh']) * 100, 2
            )
        
        # Cycle Count (may not be available)
        if hasattr(battery, 'CycleCount') and battery.CycleCount is not None:
            health_info['cycles'] = battery.CycleCount
        
        return health_info
        
    except Exception as e:
        print(f"Warning: Could not retrieve battery health: {e}")
        return None


def check_battery_health_threshold(health_info, threshold=80):
    """
    Check if battery health is below threshold
    Returns (is_below_threshold, warning_message)
    """
    if not health_info or health_info.get('health_percent') is None:
        return False, None
    
    health_percent = health_info['health_percent']
    
    if health_percent < threshold:
        warning = f"Warning: Battery health is {health_percent}% (below {threshold}% threshold)"
        return True, warning
    
    return False, None


if __name__ == '__main__':
    print("Battery Health Information:")
    print("=" * 50)
    health = get_battery_health()
    if health:
        for key, value in health.items():
            print(f"{key}: {value}")
        
        is_low, warning = check_battery_health_threshold(health)
        if is_low:
            print(f"\n{warning}")
    else:
        print("Battery health information not available")

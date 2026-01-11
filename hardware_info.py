"""
Hardware Detection Module
Collects hardware information and generates unique laptop ID
"""
import platform
import psutil
import sys

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("Warning: wmi module not available. Some hardware details may be missing.")


def get_hardware_info():
    """
    Collect comprehensive hardware information
    Returns dict with hardware details
    """
    hardware = {
        'cpu': platform.processor(),
        'cpu_cores': psutil.cpu_count(logical=False),
        'cpu_logical_cores': psutil.cpu_count(logical=True),
        'ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'system_model': platform.system(),
        'system_version': platform.version(),
        'system_serial': None,
        'manufacturer': None,
        'hdd_model': None,
        'hdd_capacity_gb': None,
    }
    
    # Try to get detailed info via WMI (Windows only)
    if WMI_AVAILABLE and platform.system() == 'Windows':
        try:
            c = wmi.WMI()
            
            # System information
            for system in c.Win32_ComputerSystem():
                hardware['system_model'] = system.Model or hardware['system_model']
                hardware['manufacturer'] = system.Manufacturer or hardware['manufacturer']
                hardware['system_serial'] = system.SerialNumber or hardware['system_serial']
            
            # CPU information
            for processor in c.Win32_Processor():
                if processor.Name:
                    hardware['cpu'] = processor.Name.strip()
                break
            
            # Disk information
            for disk in c.Win32_DiskDrive():
                if disk.MediaType == 'Fixed hard disk media' or disk.Size:
                    hardware['hdd_model'] = disk.Model or hardware['hdd_model']
                    if disk.Size:
                        hardware['hdd_capacity_gb'] = round(int(disk.Size) / (1024**3), 2)
                    break
            
        except Exception as e:
            print(f"Warning: Could not retrieve WMI data: {e}")
    
    return hardware


def get_battery_info():
    """
    Get battery information via WMI
    Returns dict with battery details or None if unavailable
    """
    if not WMI_AVAILABLE or platform.system() != 'Windows':
        return None
    
    try:
        c = wmi.WMI()
        batteries = c.Win32_Battery()
        
        if not batteries:
            return None
        
        battery = batteries[0]
        battery_info = {
            'design_capacity_mwh': battery.DesignCapacity if battery.DesignCapacity else None,
            'full_charge_capacity_mwh': battery.FullChargeCapacity if battery.FullChargeCapacity else None,
            'cycles': battery.CycleCount if hasattr(battery, 'CycleCount') and battery.CycleCount else None,
        }
        
        # Calculate health percentage
        if battery_info['design_capacity_mwh'] and battery_info['full_charge_capacity_mwh']:
            battery_info['health_percent'] = round(
                (battery_info['full_charge_capacity_mwh'] / battery_info['design_capacity_mwh']) * 100, 2
            )
        else:
            battery_info['health_percent'] = None
        
        return battery_info
    except Exception as e:
        print(f"Warning: Could not retrieve battery info: {e}")
        return None


def generate_laptop_id():
    """
    Generate unique laptop ID from hardware information
    Format: LAPTOP-{SERIAL}-{MODEL}-{CPU}
    Falls back to UUID-based ID if serial unavailable
    """
    hardware = get_hardware_info()
    
    # Try to use serial number first
    if hardware.get('system_serial') and hardware['system_serial'] != 'To be filled by O.E.M.':
        serial = hardware['system_serial'].replace(' ', '-').upper()
        model = (hardware.get('system_model') or 'UNKNOWN').replace(' ', '-').upper()
        cpu = (hardware.get('cpu') or 'UNKNOWN').split()[0] if hardware.get('cpu') else 'UNKNOWN'
        cpu = cpu.replace(' ', '-').upper()
        
        laptop_id = f"LAPTOP-{serial}-{model}-{cpu}"
        # Clean up ID (remove special chars, limit length)
        laptop_id = ''.join(c if c.isalnum() or c == '-' else '' for c in laptop_id)
        laptop_id = laptop_id[:100]  # Limit length
        return laptop_id
    else:
        # Fallback: Use UUID
        import uuid
        machine_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 
            f"{hardware.get('system_model', '')}-{hardware.get('cpu', '')}-{platform.node()}"
        ))
        return f"LAPTOP-{machine_id[:8].upper()}"


if __name__ == '__main__':
    print("Hardware Information:")
    print("=" * 50)
    hw = get_hardware_info()
    for key, value in hw.items():
        print(f"{key}: {value}")
    
    print("\nBattery Information:")
    print("=" * 50)
    bat = get_battery_info()
    if bat:
        for key, value in bat.items():
            print(f"{key}: {value}")
    else:
        print("Battery information not available")
    
    print(f"\nLaptop ID: {generate_laptop_id()}")

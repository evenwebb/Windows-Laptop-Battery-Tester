"""
Test Metadata Logger Module
Collects and logs test environment data
"""
import platform
import psutil
import sys
from datetime import datetime


def get_os_info():
    """Get OS version and build information"""
    return {
        'os_version': platform.system(),
        'os_release': platform.release(),
        'os_version_full': platform.version(),
        'os_build': platform.version().split('.')[-1] if '.' in platform.version() else None,
    }


def get_top_processes(count=5):
    """Get top CPU-consuming processes"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                proc.info['cpu_percent'] = proc.cpu_percent(interval=0.1)
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top N
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        return [p['name'] for p in processes[:count]]
    except Exception as e:
        print(f"Warning: Could not get top processes: {e}")
        return []


def check_wifi_status():
    """Check if WiFi/network is enabled"""
    try:
        # Check if any network interface is up
        interfaces = psutil.net_if_stats()
        for interface, stats in interfaces.items():
            if stats.isup and 'Wi-Fi' in interface or 'Wireless' in interface:
                return True
        return False
    except Exception as e:
        print(f"Warning: Could not check WiFi status: {e}")
        return None


def collect_test_metadata(original_power_plan=None, active_power_plan=None, screen_brightness=None, notes=None):
    """
    Collect all test environment metadata
    Returns dict with test metadata
    """
    # Import here to avoid circular dependency
    try:
        from power_manager import PowerManager
        pm = PowerManager()
        if screen_brightness is None:
            screen_brightness = pm.get_screen_brightness()
    except ImportError:
        pm = None
    
    metadata = {
        'test_start_time': datetime.now().isoformat(),
        'os_version': f"{platform.system()} {platform.release()}",
        'os_build': platform.version().split('.')[-1] if '.' in platform.version() else platform.version(),
        'original_power_plan': original_power_plan or pm.get_power_plan_name(),
        'active_power_plan': active_power_plan or 'High Performance',
        'screen_brightness': screen_brightness or pm.get_screen_brightness(),
        'wifi_enabled': check_wifi_status(),
        'script_version': '1.0.0',  # TODO: Get from version file or __init__
        'notes': notes or '',
        'top_processes': get_top_processes(5),
    }
    
    return metadata


if __name__ == '__main__':
    print("Test Metadata:")
    print("=" * 50)
    metadata = collect_test_metadata()
    for key, value in metadata.items():
        print(f"{key}: {value}")

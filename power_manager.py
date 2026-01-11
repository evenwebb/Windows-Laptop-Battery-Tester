"""
Power Management Module
Manages power settings, prevents sleep, and sets power plan
"""
import platform
import subprocess
import sys

try:
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class PowerManager:
    """Manage Windows power settings"""
    
    def __init__(self):
        self.original_power_plan = None
        self.original_sleep_settings = None
        self.is_windows = platform.system() == 'Windows'
        
    def get_current_power_plan(self):
        """Get current active power plan GUID"""
        if not self.is_windows:
            return None
        
        try:
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse output: "Power Scheme GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  (Name)"
            guid = result.stdout.split('(')[0].split(':')[1].strip()
            return guid
        except Exception as e:
            print(f"Warning: Could not get current power plan: {e}")
            return None
    
    def get_power_plan_name(self, guid=None):
        """Get power plan name from GUID"""
        if not self.is_windows:
            return None
        
        if guid is None:
            guid = self.get_current_power_plan()
        
        if not guid:
            return None
        
        try:
            result = subprocess.run(
                ['powercfg', '/list'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse output to find plan name
            for line in result.stdout.split('\n'):
                if guid.lower() in line.lower():
                    # Extract name from parentheses
                    if '(' in line and ')' in line:
                        name = line.split('(')[1].split(')')[0].strip()
                        return name
            return guid
        except Exception as e:
            print(f"Warning: Could not get power plan name: {e}")
            return guid
    
    def set_high_performance_plan(self):
        """
        Set power plan to High Performance
        Returns (success, original_plan_guid, original_plan_name)
        """
        if not self.is_windows:
            return False, None, None
        
        # Get current plan
        original_guid = self.get_current_power_plan()
        original_name = self.get_power_plan_name(original_guid)
        self.original_power_plan = original_guid
        
        # Find High Performance plan GUID
        try:
            result = subprocess.run(
                ['powercfg', '/list'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Look for High Performance plan
            high_perf_guid = None
            for line in result.stdout.split('\n'):
                if 'high performance' in line.lower() or 'high-performance' in line.lower():
                    # Extract GUID (first part before spaces)
                    parts = line.strip().split()
                    if parts:
                        high_perf_guid = parts[0]
                        break
            
            # If High Performance plan not found, try to create it
            if not high_perf_guid:
                # Try to duplicate Balanced plan and rename it
                try:
                    subprocess.run(
                        ['powercfg', '/duplicatescheme', '381b4222-f694-41f0-9685-ff5bb260df2e'],  # Balanced GUID
                        capture_output=True,
                        check=True
                    )
                    # Get the new GUID and set it
                    result = subprocess.run(
                        ['powercfg', '/list'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    # Find the newly created plan (usually the first one)
                    for line in result.stdout.split('\n'):
                        if line.strip().startswith('Power Scheme GUID:'):
                            high_perf_guid = line.split(':')[1].strip().split()[0]
                            break
                except:
                    pass
            
            # Set High Performance plan
            if high_perf_guid:
                subprocess.run(
                    ['powercfg', '/setactive', high_perf_guid],
                    capture_output=True,
                    check=True
                )
                print(f"✓ Power plan set to High Performance")
                return True, original_guid, original_name
            else:
                print("Warning: High Performance power plan not found. Using current plan.")
                return False, original_guid, original_name
                
        except Exception as e:
            print(f"Warning: Could not set High Performance plan: {e}")
            return False, original_guid, original_name
    
    def restore_power_plan(self):
        """Restore original power plan"""
        if not self.is_windows or not self.original_power_plan:
            return False
        
        try:
            subprocess.run(
                ['powercfg', '/setactive', self.original_power_plan],
                capture_output=True,
                check=True
            )
            print(f"✓ Power plan restored to original")
            return True
        except Exception as e:
            print(f"Warning: Could not restore power plan: {e}")
            return False
    
    def prevent_sleep(self):
        """Prevent system from sleeping"""
        if not self.is_windows:
            return False
        
        try:
            # Set display to never turn off
            subprocess.run(
                ['powercfg', '/change', 'monitor-timeout-ac', '0'],
                capture_output=True,
                check=True
            )
            subprocess.run(
                ['powercfg', '/change', 'monitor-timeout-dc', '0'],
                capture_output=True,
                check=True
            )
            
            # Set sleep to never
            subprocess.run(
                ['powercfg', '/change', 'standby-timeout-ac', '0'],
                capture_output=True,
                check=True
            )
            subprocess.run(
                ['powercfg', '/change', 'standby-timeout-dc', '0'],
                capture_output=True,
                check=True
            )
            
            # Set hibernate to never
            subprocess.run(
                ['powercfg', '/change', 'hibernate-timeout-ac', '0'],
                capture_output=True,
                check=True
            )
            subprocess.run(
                ['powercfg', '/change', 'hibernate-timeout-dc', '0'],
                capture_output=True,
                check=True
            )
            
            print("✓ Sleep/hibernate prevented")
            return True
        except Exception as e:
            print(f"Warning: Could not prevent sleep: {e}")
            return False
    
    def restore_sleep_settings(self):
        """Restore original sleep settings (if saved)"""
        # Note: We don't save original settings, so this is a placeholder
        # In a full implementation, you'd save and restore original values
        pass
    
    def get_screen_brightness(self):
        """Get current screen brightness percentage"""
        if not self.is_windows:
            return None
        
        try:
            # Try to get brightness via WMI
            import wmi
            c = wmi.WMI(namespace='wmi')
            brightness = c.WmiMonitorBrightness()[0].CurrentBrightness
            return brightness
        except Exception:
            pass
        
        # Fallback: return None (can't reliably get brightness without WMI)
        return None


if __name__ == '__main__':
    pm = PowerManager()
    print("Current Power Plan:")
    print("=" * 50)
    guid = pm.get_current_power_plan()
    name = pm.get_power_plan_name(guid)
    print(f"GUID: {guid}")
    print(f"Name: {name}")
    
    print("\nSetting High Performance plan...")
    success, orig_guid, orig_name = pm.set_high_performance_plan()
    print(f"Success: {success}")
    print(f"Original plan: {orig_name}")
    
    print("\nPreventing sleep...")
    pm.prevent_sleep()
    
    print("\nRestoring original plan...")
    pm.restore_power_plan()

"""
Data Logging Module
Handles JSON persistence with multi-laptop support
"""
import json
import os
from datetime import datetime
from backup_manager import BackupManager


class DataLogger:
    """Handle data persistence for battery tests"""
    
    def __init__(self, data_file='battery_test_data.json'):
        self.data_file = data_file
        self.backup_manager = BackupManager(data_file)
        self.data = self._load_data()
        self.last_log_time = None
        self.last_log_percentage = None
    
    def _load_data(self):
        """Load data from JSON file or create new structure"""
        if os.path.exists(self.data_file):
            try:
                is_valid, result = self.backup_manager.validate_json(self.data_file)
                if is_valid:
                    return result
                else:
                    print(f"Warning: Data file is corrupted: {result}")
                    print("Attempting recovery from backup...")
                    success, message = self.backup_manager.recover_from_backup()
                    if success:
                        print(f"✓ {message}")
                        return self._load_data()
                    else:
                        print(f"Recovery failed: {message}")
                        print("Creating new data file...")
            except Exception as e:
                print(f"Error loading data file: {e}")
                print("Creating new data file...")
        
        # Create new data structure
        return {
            'data_version': '1.0',
            'current_laptop_id': None,
            'script_version': '1.0.0',
            'laptops': {}
        }
    
    def _save_data(self):
        """Save data to JSON file atomically"""
        try:
            # Write to temporary file first
            temp_file = self.data_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            if os.path.exists(self.data_file):
                os.replace(temp_file, self.data_file)
            else:
                os.rename(temp_file, self.data_file)
            
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
    
    def initialize_laptop(self, laptop_id, hardware_info, battery_info):
        """Initialize laptop entry in data structure"""
        if laptop_id not in self.data['laptops']:
            self.data['laptops'][laptop_id] = {
                'laptop_id': laptop_id,
                'hardware_info': hardware_info,
                'test_runs': []
            }
        
        self.data['current_laptop_id'] = laptop_id
        self._save_data()
    
    def create_test_run(self, laptop_id, test_metadata, battery_info):
        """Create a new test run"""
        run_id = f"run_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        
        test_run = {
            'run_id': run_id,
            'test_start_time': datetime.now().isoformat(),
            'test_end_time': None,
            'status': 'in_progress',
            'total_runtime_seconds': 0,
            'resumed': False,
            'battery_info': battery_info,
            'test_metadata': test_metadata,
            'power_events': [],
            'low_battery_events': [],
            'entries': []
        }
        
        if laptop_id not in self.data['laptops']:
            raise ValueError(f"Laptop {laptop_id} not initialized")
        
        self.data['laptops'][laptop_id]['test_runs'].append(test_run)
        self._save_data()
        
        return run_id
    
    def get_current_test_run(self, laptop_id):
        """Get the current (in-progress) test run"""
        if laptop_id not in self.data['laptops']:
            return None
        
        test_runs = self.data['laptops'][laptop_id]['test_runs']
        if not test_runs:
            return None
        
        # Get the last test run
        last_run = test_runs[-1]
        if last_run['status'] == 'in_progress':
            return last_run
        
        return None
    
    def add_entry(self, laptop_id, battery_percent, elapsed_seconds, charging=False):
        """
        Add a log entry
        Returns True if entry was added (based on triggers)
        """
        test_run = self.get_current_test_run(laptop_id)
        if not test_run:
            return False
        
        # Check if we should log (every 1 minute OR every 10% drop)
        should_log = False
        
        # Time-based trigger (every 1 minute)
        if self.last_log_time is None:
            should_log = True
        else:
            time_since_last = elapsed_seconds - self.last_log_time
            if time_since_last >= 60:
                should_log = True
        
        # Percentage-based trigger (every 10% drop)
        if self.last_log_percentage is not None:
            current_10pct = int(battery_percent / 10)
            last_10pct = int(self.last_log_percentage / 10)
            if current_10pct < last_10pct:
                should_log = True
        
        if should_log:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'battery_percent': battery_percent,
                'elapsed_seconds': elapsed_seconds,
                'charging': charging
            }
            
            test_run['entries'].append(entry)
            test_run['total_runtime_seconds'] = elapsed_seconds
            
            self.last_log_time = elapsed_seconds
            self.last_log_percentage = battery_percent
            
            # Note: Periodic backup is handled by main script with configurable interval
            # This allows CLI to control backup frequency
            
            self._save_data()
            return True
        
        return False
    
    def add_power_event(self, laptop_id, event_type, ac_connected, battery_percent=None):
        """Add a power event (charging detected/stopped, test started, etc.)"""
        test_run = self.get_current_test_run(laptop_id)
        if not test_run:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'ac_connected': ac_connected,
        }
        
        if battery_percent is not None:
            event['battery_percent'] = battery_percent
        
        test_run['power_events'].append(event)
        self._save_data()
    
    def add_low_battery_event(self, laptop_id, battery_percent):
        """Add a low battery event"""
        test_run = self.get_current_test_run(laptop_id)
        if not test_run:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'battery_percent': battery_percent,
            'event': 'low_battery_warning'
        }
        
        test_run['low_battery_events'].append(event)
        self._save_data()
    
    def finalize_test_run(self, laptop_id, status, final_battery_percent=None):
        """Finalize a test run"""
        test_run = self.get_current_test_run(laptop_id)
        if not test_run:
            return
        
        test_run['test_end_time'] = datetime.now().isoformat()
        test_run['status'] = status
        
        if final_battery_percent is not None:
            # Add final entry if not already logged
            last_entry = test_run['entries'][-1] if test_run['entries'] else None
            if not last_entry or last_entry['battery_percent'] != final_battery_percent:
                self.add_entry(laptop_id, final_battery_percent, test_run['total_runtime_seconds'], False)
        
        # Create final backup
        self.backup_manager.create_backup()
        self._save_data()
    
    def mark_test_resumed(self, laptop_id):
        """Mark test run as resumed"""
        test_run = self.get_current_test_run(laptop_id)
        if test_run:
            test_run['resumed'] = True
            self._save_data()


if __name__ == '__main__':
    logger = DataLogger('test_data.json')
    
    # Test initialization
    laptop_id = 'TEST-LAPTOP-001'
    hardware_info = {'cpu': 'Test CPU', 'ram_gb': 8}
    battery_info = {'design_capacity_mwh': 50000, 'health_percent': 95}
    
    logger.initialize_laptop(laptop_id, hardware_info, battery_info)
    print(f"Initialized laptop: {laptop_id}")
    
    # Test run creation
    metadata = {'os_version': 'Windows 11', 'notes': 'Test run'}
    run_id = logger.create_test_run(laptop_id, metadata, battery_info)
    print(f"Created test run: {run_id}")
    
    # Test logging
    for i in range(5):
        logger.add_entry(laptop_id, 100 - i, i * 60, False)
    
    print(f"Added {len(logger.get_current_test_run(laptop_id)['entries'])} entries")
    
    # Cleanup
    os.remove('test_data.json')

"""
Data Backup Manager Module
Handles periodic backups and recovery
"""
import json
import os
import shutil
from datetime import datetime

try:
    from pathlib import Path
except ImportError:
    # Python 2 compatibility (unlikely but safe)
    Path = None


class BackupManager:
    """Manage data file backups and recovery"""
    
    def __init__(self, data_file='battery_test_data.json', backup_dir='backups', keep_backups=5):
        self.data_file = data_file
        self.backup_dir = backup_dir
        self.keep_backups = keep_backups
        self.last_backup_time = None
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self):
        """Create a timestamped backup of the data file"""
        if not os.path.exists(self.data_file):
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"battery_test_data_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(self.data_file, backup_path)
            self.last_backup_time = datetime.now()
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            return backup_path
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent N"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('battery_test_data_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backups.append((os.path.getmtime(filepath), filepath))
            
            # Sort by modification time (newest first)
            backups.sort(reverse=True)
            
            # Remove old backups
            for _, filepath in backups[self.keep_backups:]:
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Warning: Could not remove old backup {filepath}: {e}")
        except Exception as e:
            print(f"Warning: Could not cleanup backups: {e}")
    
    def should_backup(self, interval_minutes=5):
        """Check if it's time to create a backup"""
        if self.last_backup_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_backup_time).total_seconds()
        return elapsed >= (interval_minutes * 60)
    
    def validate_json(self, filepath):
        """Validate JSON file structure"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            if 'data_version' not in data:
                return False, "Missing data_version field"
            if 'laptops' not in data:
                return False, "Missing laptops field"
            
            return True, data
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def recover_from_backup(self):
        """Attempt to recover data from most recent backup"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('battery_test_data_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backups.append((os.path.getmtime(filepath), filepath))
            
            if not backups:
                return False, "No backups found"
            
            # Sort by modification time (newest first)
            backups.sort(reverse=True)
            
            # Try each backup until we find a valid one
            for _, backup_path in backups:
                is_valid, result = self.validate_json(backup_path)
                if is_valid:
                    # Restore the backup
                    shutil.copy2(backup_path, self.data_file)
                    return True, f"Recovered from {os.path.basename(backup_path)}"
            
            return False, "No valid backups found"
        except Exception as e:
            return False, f"Recovery error: {e}"
    
    def get_backup_list(self):
        """Get list of available backups"""
        backups = []
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('battery_test_data_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                    })
            
            backups.sort(key=lambda x: x['modified'], reverse=True)
        except Exception as e:
            print(f"Warning: Could not list backups: {e}")
        
        return backups


if __name__ == '__main__':
    manager = BackupManager()
    
    print("Backup Manager Test:")
    print("=" * 50)
    
    # Create test data file
    test_data = {'data_version': '1.0', 'laptops': {}}
    with open('battery_test_data.json', 'w') as f:
        json.dump(test_data, f)
    
    # Create backup
    backup_path = manager.create_backup()
    print(f"Backup created: {backup_path}")
    
    # List backups
    backups = manager.get_backup_list()
    print(f"\nAvailable backups: {len(backups)}")
    for backup in backups:
        print(f"  - {backup['filename']} ({backup['size']} bytes)")

"""
Resume Capability Module
Detect and resume interrupted tests
"""
from datetime import datetime

try:
    from data_logger import DataLogger
except ImportError:
    DataLogger = None


class TestResumer:
    """Handle resuming interrupted tests"""
    
    def __init__(self, data_logger):
        if data_logger is None:
            raise ValueError("data_logger is required")
        self.data_logger = data_logger
    
    def find_incomplete_test(self, laptop_id):
        """Find incomplete test for laptop"""
        return self.data_logger.get_current_test_run(laptop_id)
    
    def prompt_resume(self, test_run):
        """Prompt user to resume or start new"""
        print("\n" + "=" * 50)
        print("INCOMPLETE TEST FOUND")
        print("=" * 50)
        print(f"Test started: {test_run['test_start_time']}")
        print(f"Last entry: {len(test_run['entries'])} entries")
        if test_run['entries']:
            last_entry = test_run['entries'][-1]
            print(f"Last battery: {last_entry['battery_percent']:.1f}%")
            print(f"Runtime: {last_entry['elapsed_seconds'] / 60:.1f} minutes")
        
        print("\nOptions:")
        print("  1. Resume test")
        print("  2. Start new test")
        
        while True:
            choice = input("\nEnter choice (1 or 2): ").strip()
            if choice == '1':
                return True
            elif choice == '2':
                return False
            else:
                print("Invalid choice. Please enter 1 or 2.")
    
    def resume_test(self, laptop_id):
        """Resume an interrupted test"""
        test_run = self.find_incomplete_test(laptop_id)
        
        if not test_run:
            return None
        
        # Mark as resumed
        self.data_logger.mark_test_resumed(laptop_id)
        
        # Get last entry info
        if test_run['entries']:
            last_entry = test_run['entries'][-1]
            return {
                'start_time': datetime.fromisoformat(test_run['test_start_time']),
                'last_battery_percent': last_entry['battery_percent'],
                'last_elapsed_seconds': last_entry['elapsed_seconds'],
                'run_id': test_run['run_id'],
            }
        
        return {
            'start_time': datetime.fromisoformat(test_run['test_start_time']),
            'last_battery_percent': 100,
            'last_elapsed_seconds': 0,
            'run_id': test_run['run_id'],
        }
    
    def archive_incomplete_test(self, laptop_id):
        """Archive incomplete test by marking it as interrupted"""
        test_run = self.find_incomplete_test(laptop_id)
        if test_run:
            self.data_logger.finalize_test_run(laptop_id, 'interrupted')


if __name__ == '__main__':
    from data_logger import DataLogger
    
    logger = DataLogger('test_data.json')
    resumer = TestResumer(logger)
    
    # Test finding incomplete test
    laptop_id = 'TEST-LAPTOP-001'
    incomplete = resumer.find_incomplete_test(laptop_id)
    
    if incomplete:
        print("Incomplete test found:")
        print(f"  Run ID: {incomplete['run_id']}")
        print(f"  Entries: {len(incomplete['entries'])}")
    else:
        print("No incomplete test found")

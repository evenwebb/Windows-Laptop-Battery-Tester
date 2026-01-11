"""
Results Viewer Module
Display test results with sorting and comparison
"""
from datetime import datetime, timedelta

try:
    from data_logger import DataLogger
except ImportError:
    DataLogger = None


class ResultsViewer:
    """Display battery test results"""
    
    def __init__(self, data_logger):
        if data_logger is None:
            raise ValueError("data_logger is required")
        self.data_logger = data_logger
    
    def format_time(self, seconds):
        """Format seconds as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_test_statistics(self, test_run):
        """Calculate statistics for a test run"""
        if not test_run['entries']:
            return None
        
        entries = test_run['entries']
        total_runtime = test_run['total_runtime_seconds']
        
        # Calculate discharge rate (% per hour)
        if total_runtime > 0:
            first_percent = entries[0]['battery_percent']
            last_percent = entries[-1]['battery_percent']
            discharge_rate = ((first_percent - last_percent) / total_runtime) * 3600
        else:
            discharge_rate = 0
        
        # Find percentage milestones
        milestones = {}
        for target in [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0]:
            for entry in entries:
                if entry['battery_percent'] <= target:
                    milestones[target] = {
                        'time': entry['elapsed_seconds'],
                        'formatted_time': self.format_time(entry['elapsed_seconds'])
                    }
                    break
        
        return {
            'total_runtime': total_runtime,
            'formatted_runtime': self.format_time(total_runtime),
            'discharge_rate': discharge_rate,
            'milestones': milestones,
            'entries_count': len(entries),
            'status': test_run['status'],
        }
    
    def display_laptop_results(self, laptop_id, current_laptop_id=None):
        """Display detailed results for a laptop"""
        if laptop_id not in self.data_logger.data['laptops']:
            print(f"Laptop {laptop_id} not found")
            return
        
        laptop = self.data_logger.data['laptops'][laptop_id]
        is_current = (laptop_id == current_laptop_id)
        
        print("\n" + "=" * 70)
        if is_current:
            print(f"📱 LAPTOP: {laptop_id} (CURRENT)")
        else:
            print(f"📱 LAPTOP: {laptop_id}")
        print("=" * 70)
        
        # Hardware info
        hw = laptop['hardware_info']
        print("\nHardware Information:")
        print(f"  CPU: {hw.get('cpu', 'N/A')}")
        print(f"  RAM: {hw.get('ram_gb', 'N/A')} GB")
        print(f"  Model: {hw.get('system_model', 'N/A')}")
        
        # Test runs
        test_runs = laptop['test_runs']
        if not test_runs:
            print("\nNo test runs found.")
            return
        
        print(f"\nTest Runs: {len(test_runs)}")
        print("-" * 70)
        
        for i, test_run in enumerate(test_runs, 1):
            stats = self.get_test_statistics(test_run)
            if not stats:
                continue
            
            print(f"\nTest Run #{i}: {test_run['run_id']}")
            print(f"  Status: {test_run['status']}")
            print(f"  Start: {test_run['test_start_time']}")
            if test_run['test_end_time']:
                print(f"  End: {test_run['test_end_time']}")
            print(f"  Total Runtime: {stats['formatted_runtime']}")
            print(f"  Discharge Rate: {stats['discharge_rate']:.2f}% per hour")
            
            # Battery health
            if test_run.get('battery_info'):
                bat_info = test_run['battery_info']
                if bat_info.get('health_percent'):
                    print(f"  Battery Health: {bat_info['health_percent']:.1f}%")
            
            # Milestones
            if stats['milestones']:
                print("\n  Battery Milestones:")
                for pct in [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0]:
                    if pct in stats['milestones']:
                        print(f"    {pct:3d}%: {stats['milestones'][pct]['formatted_time']}")
    
    def display_comparison(self, sort_by='runtime'):
        """Display comparison of all laptops"""
        laptops = self.data_logger.data['laptops']
        current_laptop_id = self.data_logger.data.get('current_laptop_id')
        
        if not laptops:
            print("No laptops found in data.")
            return
        
        print("\n" + "=" * 100)
        print("LAPTOP COMPARISON")
        print("=" * 100)
        
        # Collect statistics for all laptops
        laptop_stats = []
        for laptop_id, laptop in laptops.items():
            test_runs = laptop['test_runs']
            if not test_runs:
                continue
            
            # Get latest completed test run
            latest_run = None
            for test_run in reversed(test_runs):
                if test_run['status'] in ['completed', 'low_battery_shutdown']:
                    latest_run = test_run
                    break
            
            if latest_run:
                stats = self.get_test_statistics(latest_run)
                if stats:
                    laptop_stats.append({
                        'laptop_id': laptop_id,
                        'is_current': (laptop_id == current_laptop_id),
                        'hardware': laptop['hardware_info'],
                        'stats': stats,
                        'test_run': latest_run,
                    })
        
        # Sort
        if sort_by == 'runtime':
            laptop_stats.sort(key=lambda x: x['stats']['total_runtime'], reverse=True)
        elif sort_by == 'discharge_rate':
            laptop_stats.sort(key=lambda x: x['stats']['discharge_rate'])
        elif sort_by == 'battery_health':
            laptop_stats.sort(key=lambda x: x['test_run'].get('battery_info', {}).get('health_percent') or 0, reverse=True)
        
        # Display table
        print(f"\n{'Laptop ID':<20} {'Runtime':<12} {'Discharge Rate':<15} {'Status':<20} {'Health':<10}")
        print("-" * 100)
        
        for item in laptop_stats:
            laptop_id = item['laptop_id']
            if item['is_current']:
                laptop_id = f"★ {laptop_id}"
            
            runtime = item['stats']['formatted_runtime']
            discharge = f"{item['stats']['discharge_rate']:.2f}%/hr"
            status = item['stats']['status']
            
            health = 'N/A'
            if item['test_run'].get('battery_info', {}).get('health_percent'):
                health = f"{item['test_run']['battery_info']['health_percent']:.1f}%"
            
            print(f"{laptop_id:<20} {runtime:<12} {discharge:<15} {status:<20} {health:<10}")
    
    def display_current_laptop(self):
        """Display results for current laptop"""
        current_laptop_id = self.data_logger.data.get('current_laptop_id')
        if not current_laptop_id:
            print("No current laptop set.")
            return
        
        self.display_laptop_results(current_laptop_id, current_laptop_id)


if __name__ == '__main__':
    from data_logger import DataLogger
    
    logger = DataLogger('test_data.json')
    viewer = ResultsViewer(logger)
    
    print("Results Viewer Test:")
    print("=" * 50)
    
    # Display current laptop
    viewer.display_current_laptop()
    
    # Display comparison
    viewer.display_comparison()

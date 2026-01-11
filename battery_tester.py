"""
Main Battery Tester Script
Entry point for battery testing application
"""
import sys
import argparse
import signal
import time
from datetime import datetime, timedelta
from hardware_info import get_hardware_info, get_battery_info, generate_laptop_id
from battery_monitor import BatteryMonitor
from battery_health import get_battery_health
from data_logger import DataLogger
from test_validator import TestValidator
from test_resumer import TestResumer
from power_manager import PowerManager
from charging_monitor import ChargingMonitor
from low_battery_handler import LowBatteryHandler
from metadata_logger import collect_test_metadata
from results_viewer import ResultsViewer
from report_generator import ReportGenerator


class BatteryTester:
    """Main battery tester application"""
    
    def __init__(self):
        self.data_logger = DataLogger()
        self.battery_monitor = BatteryMonitor()
        self.power_manager = PowerManager()
        self.test_validator = TestValidator()
        self.test_resumer = TestResumer(self.data_logger)
        self.results_viewer = ResultsViewer(self.data_logger)
        self.report_generator = ReportGenerator(self.data_logger)
        self.running = False
        self.test_start_time = None
        self.test_notes = None
        self.low_battery_threshold = 10
        self.backup_interval = 5
        self.skip_validation = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        if sys.platform == 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n⚠️  Interrupted by user")
        self.running = False
    
    def identify_laptop(self):
        """Identify current laptop"""
        laptop_id = generate_laptop_id()
        hardware_info = get_hardware_info()
        battery_info = get_battery_info()
        
        self.data_logger.initialize_laptop(laptop_id, hardware_info, battery_info)
        
        return laptop_id
    
    def run_validation(self, laptop_id, require_100_percent=True):
        """Run pre-test validation"""
        print("\n" + "=" * 70)
        print("PRE-TEST VALIDATION")
        print("=" * 70)
        
        is_valid, errors, warnings = self.test_validator.validate_all(
            laptop_id, self.data_logger, require_100_percent
        )
        
        self.test_validator.display_results()
        
        if not is_valid:
            return False
        
        # Ask about warnings
        if warnings:
            response = input("\nContinue despite warnings? (y/n): ").strip().lower()
            if response != 'y':
                return False
        
        return True
    
    def start_test(self, laptop_id, resume_data=None):
        """Start battery test"""
        print("\n" + "=" * 70)
        print("STARTING BATTERY TEST")
        print("=" * 70)
        
        # Set power plan to High Performance
        print("\nSetting power plan to High Performance...")
        success, orig_guid, orig_name = self.power_manager.set_high_performance_plan()
        if not success:
            print("Warning: Could not set High Performance plan")
        
        # Prevent sleep
        print("Preventing sleep/hibernate...")
        self.power_manager.prevent_sleep()
        
        # Collect metadata
        metadata = collect_test_metadata(
            original_power_plan=orig_name,
            active_power_plan='High Performance',
            notes=self.test_notes
        )
        
        # Get battery info
        battery_info = get_battery_health()
        
        # Create test run
        if resume_data:
            # Resume existing test
            run_id = resume_data['run_id']
            test_run = self.data_logger.get_current_test_run(laptop_id)
            if test_run:
                test_run['resumed'] = True
                self.test_start_time = resume_data['start_time']
                print(f"Resuming test run: {run_id}")
        else:
            # New test run
            run_id = self.data_logger.create_test_run(laptop_id, metadata, battery_info)
            self.test_start_time = datetime.now()
            print(f"Created test run: {run_id}")
        
        # Wait for battery power
        print("\nWaiting for AC power to be disconnected...")
        if not self.battery_monitor.wait_for_battery_power():
            return False
        
        # Log test start event
        status = self.battery_monitor.get_battery_status()
        self.data_logger.add_power_event(
            laptop_id, 'test_started', False, status['percentage']
        )
        
        # Initialize monitoring with configured threshold
        charging_monitor = ChargingMonitor()
        low_battery_handler = LowBatteryHandler(low_battery_threshold=self.low_battery_threshold)
        
        # Update backup manager interval
        self.data_logger.backup_manager.keep_backups = 5  # Keep last 5 backups
        
        # Track pause time for charging events
        pause_start_time = None
        total_pause_time = 0
        
        # Start test loop
        print("\n" + "=" * 70)
        print("TEST IN PROGRESS")
        print("=" * 70)
        print("Press Ctrl+C to stop test\n")
        
        self.running = True
        last_battery_percent = None
        
        try:
            while self.running:
                # Get current status
                status = self.battery_monitor.get_battery_status()
                battery_percent = status['percentage']
                
                if battery_percent is None:
                    print("Warning: Battery status unavailable")
                    time.sleep(10)
                    continue
                
                # Handle charging pause/resume
                if charging_monitor.is_paused:
                    if pause_start_time is None:
                        pause_start_time = datetime.now()
                else:
                    if pause_start_time is not None:
                        # Resume from pause - add pause duration to total
                        pause_duration = (datetime.now() - pause_start_time).total_seconds()
                        total_pause_time += pause_duration
                        pause_start_time = None
                
                # Calculate elapsed time (excluding pause time)
                if resume_data:
                    base_elapsed = resume_data['last_elapsed_seconds']
                    current_time = (datetime.now() - resume_data['start_time']).total_seconds()
                else:
                    base_elapsed = 0
                    current_time = (datetime.now() - self.test_start_time).total_seconds()
                
                elapsed = base_elapsed + current_time - total_pause_time
                
                # If currently paused, don't increment elapsed time
                if pause_start_time is not None:
                    elapsed -= (datetime.now() - pause_start_time).total_seconds()
                
                # Check for charging
                if charging_monitor.check_charging_status():
                    if not charging_monitor.is_paused:
                        event = charging_monitor.handle_charging_detected()
                        if event:
                            self.data_logger.add_power_event(
                                laptop_id, 'charging_detected', True, battery_percent
                            )
                else:
                    if charging_monitor.is_paused:
                        event = charging_monitor.handle_charging_stopped()
                        if event:
                            self.data_logger.add_power_event(
                                laptop_id, 'charging_stopped', False, battery_percent
                            )
                
                # Check low battery
                is_low, low_event = low_battery_handler.check_low_battery(battery_percent)
                if is_low and low_event:
                    self.data_logger.add_low_battery_event(laptop_id, battery_percent)
                
                # Log entry (if triggered)
                logged = self.data_logger.add_entry(
                    laptop_id, battery_percent, elapsed, status['charging']
                )
                
                # Periodic backup (check interval from config)
                if self.data_logger.backup_manager.should_backup(interval_minutes=self.backup_interval):
                    self.data_logger.backup_manager.create_backup()
                
                if logged:
                    # Display status
                    runtime_str = self.results_viewer.format_time(elapsed)
                    print(f"[{runtime_str}] Battery: {battery_percent:.1f}% | "
                          f"Elapsed: {elapsed/3600:.2f} hours")
                
                # Check if battery is depleted
                if battery_percent <= 0:
                    print("\n✓ Battery depleted. Test complete.")
                    break
                
                last_battery_percent = battery_percent
                time.sleep(10)  # Poll every 10 seconds
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
        
        finally:
            # Finalize test
            final_status = low_battery_handler.determine_test_status(
                last_battery_percent, elapsed
            )
            
            self.data_logger.finalize_test_run(laptop_id, final_status, last_battery_percent)
            
            # Restore power settings
            print("\nRestoring power settings...")
            self.power_manager.restore_power_plan()
            
            # Generate report (auto-open disabled by default, can be enabled)
            print("\nGenerating report...")
            try:
                report_path = self.report_generator.generate_report(laptop_id, run_id)
                print(f"✓ Report generated: {report_path}")
                # Optionally auto-open (set to True to enable)
                auto_open = False
                if auto_open:
                    self.report_generator.generate_report_and_open(laptop_id, run_id, report_path, auto_open=True)
            except Exception as e:
                print(f"Warning: Could not generate report: {e}")
            
            print("\n" + "=" * 70)
            print("TEST COMPLETE")
            print("=" * 70)
            
            # Display results
            self.results_viewer.display_laptop_results(laptop_id, laptop_id)
    
    def handle_list_command(self):
        """Handle --list command"""
        self.results_viewer.display_comparison()
    
    def handle_compare_command(self, sort_by='runtime'):
        """Handle --compare command"""
        self.results_viewer.display_comparison(sort_by=sort_by)
    
    def handle_report_comparison_command(self, auto_open=False):
        """Handle --report-comparison command"""
        try:
            report_path = self.report_generator.generate_comparison_report()
            print(f"✓ Comparison report generated: {report_path}")
            if auto_open:
                self.report_generator.generate_report_and_open(None, None, report_path, auto_open=True)
        except Exception as e:
            print(f"Error generating comparison report: {e}")
    
    def handle_report_command(self, laptop_id=None, auto_open=False):
        """Handle --report command"""
        if laptop_id is None:
            laptop_id = self.data_logger.data.get('current_laptop_id')
            if not laptop_id:
                print("No current laptop set. Please specify laptop_id.")
                return
        
        try:
            if auto_open:
                report_path = self.report_generator.generate_report_and_open(laptop_id, None, None, auto_open=True)
            else:
                report_path = self.report_generator.generate_report(laptop_id)
            print(f"✓ Report generated: {report_path}")
        except Exception as e:
            print(f"Error generating report: {e}")
    
    def handle_current_command(self):
        """Handle --current command"""
        self.results_viewer.display_current_laptop()
    
    def handle_history_command(self, laptop_id=None):
        """Handle --history command"""
        if laptop_id is None:
            laptop_id = self.data_logger.data.get('current_laptop_id')
            if not laptop_id:
                print("No current laptop set. Please specify laptop_id.")
                return
        
        self.results_viewer.display_laptop_results(laptop_id, laptop_id)
    
    def run(self):
        """Main run method"""
        parser = argparse.ArgumentParser(
            description='Windows Laptop Battery Tester - Monitor battery discharge and generate reports',
            epilog='''
Examples:
  battery_tester.exe                    # Start new test (interactive)
  battery_tester.exe --list             # Show all laptops summary
  battery_tester.exe --compare          # Compare all laptops sorted by runtime
  battery_tester.exe --current          # Show current laptop results
  battery_tester.exe --report           # Generate report for current laptop
  battery_tester.exe --report LAPTOP-123 # Generate report for specific laptop
  battery_tester.exe --resume           # Resume interrupted test
  battery_tester.exe --validate         # Run pre-test checks only
  battery_tester.exe --notes "Test after battery replacement"
  battery_tester.exe --history LAPTOP-123 # Show test history
  battery_tester.exe --auto-open        # Auto-open report after generation
  battery_tester.exe --low-battery 15   # Set low battery threshold to 15%%
  battery_tester.exe --backup-interval 10 # Backup every 10 minutes
            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Information commands
        parser.add_argument('--list', action='store_true',
                          help='Show all tested laptops with summary statistics')
        parser.add_argument('--compare', action='store_true',
                          help='Show comparison view sorted by runtime (use --sort to change)')
        parser.add_argument('--current', action='store_true',
                          help='Show only current laptop\'s detailed results')
        parser.add_argument('--history', nargs='?', const=True, metavar='LAPTOP_ID',
                          help='Show test history for laptop (or current if omitted)')
        
        # Report commands
        parser.add_argument('--report', nargs='?', const=True, metavar='LAPTOP_ID',
                          help='Generate JPEG report for laptop (or current if omitted)')
        parser.add_argument('--report-comparison', action='store_true',
                          help='Generate comparison report for all laptops')
        parser.add_argument('--auto-open', action='store_true',
                          help='Automatically open generated reports')
        
        # Test control
        parser.add_argument('--resume', action='store_true',
                          help='Resume interrupted test (skip confirmation prompt)')
        parser.add_argument('--validate', action='store_true',
                          help='Run pre-test validation checks only (don\'t start test)')
        parser.add_argument('--notes', type=str, metavar='TEXT',
                          help='Add notes/comments to test run (use quotes for spaces)')
        
        # Configuration options
        parser.add_argument('--low-battery', type=int, metavar='PERCENT', default=10,
                          help='Low battery warning threshold (default: 10%%)')
        parser.add_argument('--backup-interval', type=int, metavar='MINUTES', default=5,
                          help='Backup interval in minutes (default: 5)')
        parser.add_argument('--skip-validation', action='store_true',
                          help='Skip pre-test validation (use with caution)')
        parser.add_argument('--sort', choices=['runtime', 'discharge_rate', 'battery_health'],
                          default='runtime', metavar='FIELD',
                          help='Sort field for comparison view (default: runtime)')
        
        # Utility
        parser.add_argument('--version', action='version', version='Battery Tester 1.0.0')
        
        args = parser.parse_args()
        
        # Handle command-line commands (information/viewing)
        if args.list:
            self.handle_list_command()
            return
        
        if args.compare:
            self.handle_compare_command(sort_by=args.sort)
            return
        
        if args.report:
            laptop_id = args.report if isinstance(args.report, str) else None
            self.handle_report_command(laptop_id, auto_open=args.auto_open)
            return
        
        if args.report_comparison:
            self.handle_report_comparison_command(auto_open=args.auto_open)
            return
        
        if args.current:
            self.handle_current_command()
            return
        
        if args.history:
            laptop_id = args.history if isinstance(args.history, str) else None
            self.handle_history_command(laptop_id)
            return
        
        # Store configuration
        if args.notes:
            self.test_notes = args.notes
        
        self.low_battery_threshold = args.low_battery
        self.backup_interval = args.backup_interval
        self.skip_validation = args.skip_validation
        
        # Identify laptop
        laptop_id = self.identify_laptop()
        print(f"\nCurrent Laptop: {laptop_id}")
        
        # Check for existing data and show results if available
        if self.data_logger.data.get('laptops'):
            # Show results with sorting options
            print("\n" + "=" * 70)
            print("EXISTING TEST DATA FOUND")
            print("=" * 70)
            self.results_viewer.display_comparison(sort_by='runtime')
            print("\n" + "=" * 70)
        
        # Check for incomplete test
        incomplete_test = self.test_resumer.find_incomplete_test(laptop_id)
        resume_data = None
        
        if incomplete_test:
            if args.resume:
                resume_data = self.test_resumer.resume_test(laptop_id)
            else:
                if self.test_resumer.prompt_resume(incomplete_test):
                    resume_data = self.test_resumer.resume_test(laptop_id)
                else:
                    self.test_resumer.archive_incomplete_test(laptop_id)
        
        # Run validation
        if args.validate:
            self.run_validation(laptop_id)
            return
        
        if not resume_data and not self.skip_validation:
            if not self.run_validation(laptop_id):
                print("\nValidation failed. Please fix errors and try again.")
                return
        elif self.skip_validation:
            print("\n⚠️  Warning: Validation skipped. Test may not be accurate.")
        
        # Start test
        self.start_test(laptop_id, resume_data)


def main():
    """Main entry point"""
    try:
        tester = BatteryTester()
        tester.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

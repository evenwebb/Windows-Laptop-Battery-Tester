"""
Main Battery Tester Script
Entry point for battery testing application
"""
import argparse
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime
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
from discharge_analyzer import DischargeAnalyzer
from power_event_logger import PowerEventLogger
from test_config import TestConfig, PRESETS

# Global debug logger
debug_logger = None
DEBUG_MODE = False


def setup_debug_logging():
    """Setup debug logging to file"""
    global debug_logger, DEBUG_MODE
    
    DEBUG_MODE = True
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'battery_tester_debug_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also print to console
        ]
    )
    
    debug_logger = logging.getLogger('battery_tester')
    debug_logger.info("=" * 70)
    debug_logger.info("DEBUG MODE ENABLED")
    debug_logger.info("=" * 70)
    debug_logger.info(f"Log file: {os.path.abspath(log_file)}")
    debug_logger.info(f"Python version: {sys.version}")
    debug_logger.info(f"Platform: {sys.platform}")
    debug_logger.info(f"Command line arguments: {sys.argv}")
    debug_logger.info("=" * 70)
    
    print(f"\n[DEBUG] Logging enabled. Log file: {os.path.abspath(log_file)}\n")
    
    return debug_logger


def log_debug(message, level='info'):
    """Log a debug message if debug mode is enabled"""
    global debug_logger, DEBUG_MODE
    
    if DEBUG_MODE and debug_logger:
        if level == 'debug':
            debug_logger.debug(message)
        elif level == 'info':
            debug_logger.info(message)
        elif level == 'warning':
            debug_logger.warning(message)
        elif level == 'error':
            debug_logger.error(message)
        elif level == 'critical':
            debug_logger.critical(message)
        elif level == 'exception':
            debug_logger.exception(message)


class BatteryTester:
    """Main battery tester application"""
    
    def __init__(self):
        log_debug("Initializing BatteryTester", 'info')

        self.config = TestConfig()
        self.data_logger = DataLogger()
        log_debug(f"DataLogger initialized. Data file: {self.data_logger.data_file}", 'debug')

        self.battery_monitor = BatteryMonitor()
        log_debug("BatteryMonitor initialized", 'debug')

        self.power_manager = PowerManager()
        log_debug("PowerManager initialized", 'debug')

        self.test_validator = TestValidator()
        log_debug("TestValidator initialized", 'debug')

        self.test_resumer = TestResumer(self.data_logger)
        log_debug("TestResumer initialized", 'debug')

        self.results_viewer = ResultsViewer(self.data_logger)
        log_debug("ResultsViewer initialized", 'debug')

        self.report_generator = ReportGenerator(self.data_logger)
        log_debug("ReportGenerator initialized", 'debug')

        self.running = False
        self.test_start_time = None
        self.test_notes = None
        self.low_battery_threshold = self.config.get('low_battery_threshold', 10)
        self.backup_interval = self.config.get('backup_interval', 5)
        self.skip_validation = False
        self.selected_preset = None
        self.csv_export = self.config.get('csv_export', False)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        if sys.platform == 'win32':
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        log_debug("BatteryTester initialization complete", 'info')
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        log_debug(f"Signal received: {signum}", 'warning')
        print("\n\n⚠️  Interrupted by user")
        self.running = False
    
    def identify_laptop(self):
        """Identify current laptop"""
        log_debug("Identifying laptop...", 'info')
        
        laptop_id = generate_laptop_id()
        log_debug(f"Generated laptop ID: {laptop_id}", 'info')
        
        hardware_info = get_hardware_info()
        log_debug(f"Hardware info: {hardware_info}", 'debug')
        
        battery_info = get_battery_info()
        log_debug(f"Battery info: {battery_info}", 'debug')
        
        self.data_logger.initialize_laptop(laptop_id, hardware_info, battery_info)
        log_debug(f"Laptop initialized in data logger", 'info')
        
        return laptop_id
    
    def run_validation(self, laptop_id, require_100_percent=True, interactive=True):
        """Run pre-test validation"""
        log_debug(f"Running validation for laptop: {laptop_id}", 'info')

        print("\n" + "=" * 70)
        print("PRE-TEST VALIDATION")
        print("=" * 70)

        is_valid, errors, warnings = self.test_validator.validate_all(
            laptop_id, self.data_logger, require_100_percent
        )

        log_debug(f"Validation result - Valid: {is_valid}, Errors: {len(errors)}, Warnings: {len(warnings)}", 'info')
        self.test_validator.display_results()

        if not is_valid:
            log_debug("Validation failed", 'error')
            if interactive:
                ok = self._prompt_yes_no_choice(
                    "VALIDATION FAILED",
                    [("Continue anyway (not recommended)", True),
                     ("Exit and fix issues", False)],
                    confirm_on=0,
                )
                if ok:
                    return True
                return False
            return False

        if warnings:
            log_debug("Validation has warnings, prompting user", 'info')
            if interactive:
                ok = self._prompt_yes_no_choice(
                    "VALIDATION WARNINGS",
                    [("Continue despite warnings", True),
                     ("Exit and fix warnings", False)],
                )
                if ok:
                    return True
                return False
            else:
                response = input("\nContinue despite warnings? (y/n): ").strip().lower()
                if response != 'y':
                    return False

        log_debug("Validation passed", 'info')
        return True

    def _prompt_yes_no_choice(self, title, options, confirm_on=None):
        """Show a numbered choice prompt. Returns True/False or None if interrupted."""
        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)
        print()
        for i, (label, _) in enumerate(options, 1):
            print(f"  {i}. {label}")
        while True:
            try:
                choice = input("\nSelect option: ").strip()
                log_debug(f"User selected: {choice}", 'debug')
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    if confirm_on is not None and idx == confirm_on:
                        conf = input(f"\n⚠️  {options[idx][0]}. Are you sure? (yes/no): ").strip().lower()
                        if conf != 'yes':
                            return False
                    return options[idx][1]
                print(f"Invalid choice. Please enter 1-{len(options)}.")
            except ValueError:
                print(f"Invalid input. Please enter 1-{len(options)}.")
            except (KeyboardInterrupt, EOFError):
                return False
    
    def start_test(self, laptop_id, resume_data=None, auto_start=False):
        """Start battery test"""
        log_debug(f"Starting battery test for laptop: {laptop_id}", 'info')
        if resume_data:
            log_debug(f"Resuming test with data: {resume_data}", 'info')

        W = 70

        print("\n" + "=" * W)
        print("  BATTERY TEST SETUP")
        print("=" * W)
        print("  Setting power plan to High Performance...", end=' ')
        success, orig_guid, orig_name = self.power_manager.set_high_performance_plan()
        print("OK" if success else "skipped")
        print("  Preventing sleep/hibernate...", end=' ')
        self.power_manager.prevent_sleep()
        print("OK")

        metadata = collect_test_metadata(original_power_plan=orig_name, active_power_plan='High Performance', notes=self.test_notes)
        battery_info = get_battery_health()

        run_id = None
        if resume_data:
            run_id = resume_data['run_id']
            test_run = self.data_logger.get_current_test_run(laptop_id)
            if test_run:
                test_run['resumed'] = True
                self.test_start_time = resume_data['start_time']
                print(f"\n  Resuming test run: {run_id}")
        else:
            run_id = self.data_logger.create_test_run(laptop_id, metadata, battery_info)
            self.test_start_time = datetime.now()
            print(f"\n  Test run: {run_id}")

        if auto_start and not resume_data:
            print("\n" + "=" * W)
            print("  AUTO-START MODE")
            print("=" * W)
            print("  Waiting for AC power to be disconnected...")
            print("  (Plug in now, then disconnect to begin automatically)\n")
            self.battery_monitor.wait_for_battery_power()
            self.test_start_time = datetime.now()
            status = self.battery_monitor.get_battery_status()
            print(f"\n  ✓ Battery power detected at {self.test_start_time.strftime('%H:%M:%S')}")
            print(f"  Starting battery: {status['percentage']:.1f}%\n")
        else:
            print("\n  Waiting for AC power to be disconnected...")
            if not self.battery_monitor.wait_for_battery_power():
                return False

        status = self.battery_monitor.get_battery_status()
        self.data_logger.add_power_event(laptop_id, 'test_started', False, status['percentage'])

        charging_monitor = ChargingMonitor(grace_period=30)
        low_battery_handler = LowBatteryHandler(low_battery_threshold=self.low_battery_threshold)
        discharge = DischargeAnalyzer()
        power_events = PowerEventLogger()
        self.data_logger.backup_manager.keep_backups = 5

        max_duration = None
        if self.selected_preset and self.selected_preset != 'full_discharge':
            preset = PRESETS[self.selected_preset]
            max_duration = preset.get('max_duration_minutes')

        total_pause_time = 0
        pause_start_time = None

        preset_label = f" [{PRESETS[self.selected_preset]['name']}]" if self.selected_preset else ""
        print()
        print("=" * W)
        print(f"  TEST IN PROGRESS{preset_label}")
        print("=" * W)
        print(f"  {'Runtime':>8s}  {'Batt':>6s}  {'Rate':>7s}  {'Est':>10s}  {'Status'}")
        print("-" * W)

        self.running = True
        last_battery_percent = None

        try:
            while self.running:
                status = self.battery_monitor.get_battery_status()
                battery_percent = status['percentage']
                if battery_percent is None:
                    time.sleep(5)
                    continue

                charge_state = charging_monitor.update()

                if charge_state == 'paused' and pause_start_time is None:
                    pause_start_time = datetime.now()
                    print(f"\n  ⏸  Charger connected. Test paused. Disconnect to resume.")
                elif charge_state == 'resumed':
                    if pause_start_time is not None:
                        pd = (datetime.now() - pause_start_time).total_seconds()
                        total_pause_time += pd
                        pause_start_time = None
                        print(f"\n  ▶  Resumed (+{pd/60:.1f}min pause)")

                if resume_data:
                    base_elapsed = resume_data['last_elapsed_seconds']
                    current_time = (datetime.now() - resume_data['start_time']).total_seconds()
                else:
                    base_elapsed = 0
                    current_time = (datetime.now() - self.test_start_time).total_seconds()

                elapsed = base_elapsed + current_time - total_pause_time
                if pause_start_time is not None:
                    elapsed -= (datetime.now() - pause_start_time).total_seconds()

                sys_event = power_events.poll()
                if sys_event:
                    self.data_logger.add_power_event(laptop_id, 'system_' + sys_event['event'], sys_event['event'] == 'ac_connected', sys_event.get('battery_percent'))

                if not charging_monitor.is_paused:
                    rate, eta_mins = discharge.update(battery_percent, elapsed)
                else:
                    rate, eta_mins = 0, 0

                is_low, low_event = low_battery_handler.check_low_battery(battery_percent)
                if is_low and low_event:
                    self.data_logger.add_low_battery_event(laptop_id, battery_percent)

                logged = self.data_logger.add_entry(laptop_id, battery_percent, elapsed, status['charging'])
                if self.data_logger.backup_manager.should_backup(interval_minutes=self.backup_interval):
                    self.data_logger.backup_manager.create_backup()

                if logged:
                    runtime_str = self.results_viewer.format_time(elapsed)
                    bar = _battery_bar(battery_percent, 20)
                    state = '⏸ PAUSED' if charging_monitor.is_paused else '▶ RUNNING'
                    rate_str = f"{rate:.1f}%/h" if rate > 0 else " -- "
                    if eta_mins > 0 and eta_mins < 1440:
                        eh, em = int(eta_mins // 60), int(eta_mins % 60)
                        eta_str = f"{eh}h{em:02d}m"
                    else:
                        eta_str = " -- "
                    print(f"  {runtime_str:>8s}  {battery_percent:5.1f}% {bar}  {rate_str:>7s}  {eta_str:>10s}  {state}")

                if charge_state == 'grace':
                    gr = charging_monitor.grace_remaining
                    if 0 < gr <= 10:
                        print(f"  ⚡ Charger detected! Pausing in {gr}s unless disconnected...")

                if battery_percent <= 0:
                    print("\n  ✓ Battery depleted. Test complete.")
                    break
                if max_duration and elapsed >= max_duration * 60:
                    rf, _ = discharge.update(battery_percent, elapsed)
                    est_total = battery_percent / rf * 3600 if rf > 0 else 0
                    print(f"\n  ✓ Quick test complete. Est full runtime: {est_total/3600:.1f}h")
                    break

                last_battery_percent = battery_percent
                time.sleep(self.config.get('log_interval_seconds', 10))
        except KeyboardInterrupt:
            print("\n\n  ⚠  Test interrupted by user")
        finally:
            final_status = low_battery_handler.determine_test_status(last_battery_percent)
            self.data_logger.finalize_test_run(laptop_id, final_status, last_battery_percent)

            print("\n  Restoring power settings...", end=' ')
            self.power_manager.restore_power_plan()
            print("OK")

            summary = discharge.get_summary()
            print(f"\n  Discharge Statistics:")
            print(f"    Avg rate:  {summary['avg_rate_percent_per_hour']}%/hr")
            print(f"    Peak rate: {summary['short_term_rate_percent_per_hour']}%/hr")

            if run_id:
                print("\n  Generating report...", end=' ')
                try:
                    report_path = self.report_generator.generate_report(laptop_id, run_id)
                    print(f"OK\n  {report_path}")
                    if self.config.get('auto_open_report', False):
                        self.report_generator._open_report(report_path)
                except Exception as e:
                    print(f"skipped ({e})")

            if self.csv_export and run_id:
                try:
                    self.results_viewer.export_csv(laptop_id, run_id)
                except Exception as e:
                    print(f"  CSV export: skipped ({e})")

            self.config.save()
            print("\n" + "=" * W)
            print("  TEST COMPLETE")
            print("=" * W)
            self.results_viewer.display_laptop_results(laptop_id, laptop_id)
        
        print("\n" + "=" * 70)
        print("STARTING BATTERY TEST")
        print("=" * 70)
        
        # Set power plan to High Performance
        print("\nSetting power plan to High Performance...")
        log_debug("Attempting to set power plan to High Performance", 'info')
        success, orig_guid, orig_name = self.power_manager.set_high_performance_plan()
        log_debug(f"Power plan change result: success={success}, original={orig_name}", 'info')
        if not success:
            log_debug("Failed to set High Performance plan", 'warning')
            print("Warning: Could not set High Performance plan")
        
        # Prevent sleep
        print("Preventing sleep/hibernate...")
        log_debug("Preventing sleep/hibernate", 'info')
        sleep_result = self.power_manager.prevent_sleep()
        log_debug(f"Sleep prevention result: {sleep_result}", 'info')
        
        # Collect metadata
        metadata = collect_test_metadata(
            original_power_plan=orig_name,
            active_power_plan='High Performance',
            notes=self.test_notes
        )
        
        # Get battery info
        battery_info = get_battery_health()
        
        run_id = None
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
                self.report_generator._open_report(report_path)
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
    
    def _run_start_test_interactive(self, auto_start=False):
        """Interactive start test flow"""
        print("\n" + "=" * 70)
        print("START NEW BATTERY TEST")
        print("=" * 70)
        
        # Identify laptop
        laptop_id = self.identify_laptop()
        print(f"\nCurrent Laptop: {laptop_id}")
        
        # Check for existing data
        if self.data_logger.data.get('laptops'):
            print("\n" + "=" * 70)
            print("EXISTING TEST DATA FOUND")
            print("=" * 70)
            self.results_viewer.display_comparison(sort_by='runtime')
            print("\n" + "=" * 70)
        
        # Check for incomplete test
        incomplete_test = self.test_resumer.find_incomplete_test(laptop_id)
        if incomplete_test:
            print("\n⚠️  Incomplete test found!")
            if self.test_resumer.prompt_resume(incomplete_test):
                resume_data = self.test_resumer.resume_test(laptop_id)
                self.start_test(laptop_id, resume_data, auto_start=auto_start)
                return
            else:
                self.test_resumer.archive_incomplete_test(laptop_id)
        
        # Get optional notes
        try:
            notes = input("\nEnter test notes (optional, press Enter to skip): ").strip()
            if notes:
                self.test_notes = notes
        except (KeyboardInterrupt, EOFError):
            pass
        
        # Run validation
        if not self.run_validation(laptop_id, require_100_percent=True, interactive=True):
            print("\nTest cancelled due to validation errors.")
            return
        
        # Start test
        self.start_test(laptop_id, None, auto_start=auto_start)
    
    def _run_resume_interactive(self):
        """Interactive resume test flow"""
        print("\n" + "=" * 70)
        print("RESUME INTERRUPTED TEST")
        print("=" * 70)
        
        try:
            laptop_id = self.identify_laptop()
            incomplete_test = self.test_resumer.find_incomplete_test(laptop_id)
            
            if not incomplete_test:
                print("\nNo incomplete test found for this laptop.")
                return
            
            if self.test_resumer.prompt_resume(incomplete_test):
                resume_data = self.test_resumer.resume_test(laptop_id)
                self.start_test(laptop_id, resume_data)
            else:
                print("\nResume cancelled.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            raise
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
            raise
    
    def _run_view_results_interactive(self):
        """Interactive view results flow"""
        print("\n" + "=" * 70)
        print("VIEW TEST RESULTS")
        print("=" * 70)
        
        try:
            laptop_id = self.data_logger.data.get('current_laptop_id')
            
            if not laptop_id:
                # Show list of laptops
                if not self.data_logger.data.get('laptops'):
                    print("\nNo test data found.")
                    return
                
                print("\nAvailable laptops:")
                laptops = list(self.data_logger.data['laptops'].keys())
                for i, lid in enumerate(laptops, 1):
                    print(f"  {i}. {lid}")
                
                try:
                    choice = input("\nSelect laptop number (or press Enter for current): ").strip()
                    if choice:
                        idx = int(choice) - 1
                        if 0 <= idx < len(laptops):
                            laptop_id = laptops[idx]
                        else:
                            print("Invalid selection.")
                            return
                except (ValueError, KeyboardInterrupt, EOFError):
                    return
            
            if laptop_id:
                self.results_viewer.display_laptop_results(laptop_id, laptop_id)
            else:
                print("\nNo laptop selected.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            raise
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
            raise
    
    def _run_report_interactive(self):
        """Interactive report generation flow"""
        print("\n" + "=" * 70)
        print("GENERATE REPORT")
        print("=" * 70)
        
        try:
            laptop_id = self.data_logger.data.get('current_laptop_id')
            
            if not laptop_id or laptop_id not in self.data_logger.data.get('laptops', {}):
                # Show list of laptops
                if not self.data_logger.data.get('laptops'):
                    print("\nNo test data found.")
                    return
                
                print("\nAvailable laptops:")
                laptops = list(self.data_logger.data['laptops'].keys())
                for i, lid in enumerate(laptops, 1):
                    print(f"  {i}. {lid}")
                
                try:
                    choice = input("\nSelect laptop number: ").strip()
                    if choice:
                        idx = int(choice) - 1
                        if 0 <= idx < len(laptops):
                            laptop_id = laptops[idx]
                        else:
                            print("Invalid selection.")
                            return
                    else:
                        print("No laptop selected.")
                        return
                except (ValueError, KeyboardInterrupt, EOFError):
                    return
            
            try:
                auto_open = input("\nOpen report after generation? (y/n): ").strip().lower() == 'y'
                self.handle_report_command(laptop_id, auto_open=auto_open)
            except (KeyboardInterrupt, EOFError):
                print("\nReport generation cancelled.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            raise
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
            raise
    
    def _run_validate_interactive(self):
        """Interactive validation flow"""
        try:
            laptop_id = self.identify_laptop()
            print(f"\nCurrent Laptop: {laptop_id}")
            
            is_valid = self.run_validation(laptop_id, require_100_percent=True, interactive=True)
            
            if is_valid:
                print("\n✓ All validation checks passed!")
                print("You can now start a battery test.")
            else:
                print("\n✗ Validation failed. Please fix the issues before starting a test.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            raise
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
            raise
    
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
        parser.add_argument('--auto-start', action='store_true',
                          help='Auto-start test when AC power is disconnected')
        parser.add_argument('--skip-validation', action='store_true',
                          help='Skip pre-test validation (use with caution)')
        parser.add_argument('--sort', choices=['runtime', 'discharge_rate', 'battery_health'],
                          default='runtime', metavar='FIELD',
                          help='Sort field for comparison view (default: runtime)')
        parser.add_argument('--preset', choices=list(PRESETS.keys()),
                          metavar='PRESET', help='Test preset: ' + ', '.join(PRESETS.keys()))
        parser.add_argument('--export-csv', action='store_true',
                          help='Export test results to CSV after completion')
        parser.add_argument('--config', nargs='?', const='show', metavar='KEY=VALUE',
                          help='Show or set config (e.g. --config low_battery_threshold=15)')
        parser.add_argument('--debug', action='store_true',
                          help='Enable debug logging to file (logs/battery_tester_debug_*.log)')
        
        # Utility
        parser.add_argument('--version', action='version', version='Battery Tester 1.0.0')
        
        args = parser.parse_args()
        
        # Enable debug logging if requested
        if args.debug:
            setup_debug_logging()
            log_debug("Debug mode enabled via command-line argument", 'info')

        # Handle --config
        if args.config:
            if args.config == 'show':
                self.config.show()
                return
            if '=' in args.config:
                key, _, val = args.config.partition('=')
                key = key.strip()
                val = val.strip()
                if val.isdigit():
                    val = int(val)
                elif val.lower() in ('true', 'false'):
                    val = val.lower() == 'true'
                self.config.set(key, val)
                print(f"  Set {key} = {val} (saved)")
                return
            self.config.show()
            return

        # Store configuration
        if args.notes:
            self.test_notes = args.notes
            self.config.set('notes', args.notes)
            log_debug(f"Test notes set: {args.notes}", 'info')

        self.csv_export = args.export_csv
        self.selected_preset = args.preset

        self.low_battery_threshold = args.low_battery
        self.config.set('low_battery_threshold', args.low_battery)
        log_debug(f"Low battery threshold set to: {args.low_battery}%", 'debug')

        self.backup_interval = args.backup_interval
        self.config.set('backup_interval', args.backup_interval)
        log_debug(f"Backup interval set to: {args.backup_interval} minutes", 'debug')

        self.skip_validation = args.skip_validation
        if args.skip_validation:
            log_debug("Validation skipping enabled", 'warning')
        
        # Handle command-line commands (information/viewing)
        try:
            if args.list:
                log_debug("Executing --list command", 'info')
                self.handle_list_command()
                return
            
            if args.compare:
                log_debug(f"Executing --compare command (sort: {args.sort})", 'info')
                self.handle_compare_command(sort_by=args.sort)
                return
            
            if args.report:
                laptop_id = args.report if isinstance(args.report, str) else None
                log_debug(f"Executing --report command (laptop_id: {laptop_id}, auto_open: {args.auto_open})", 'info')
                self.handle_report_command(laptop_id, auto_open=args.auto_open)
                return
            
            if args.report_comparison:
                log_debug(f"Executing --report-comparison command (auto_open: {args.auto_open})", 'info')
                self.handle_report_comparison_command(auto_open=args.auto_open)
                return
            
            if args.current:
                log_debug("Executing --current command", 'info')
                self.handle_current_command()
                return
            
            if args.history:
                laptop_id = args.history if isinstance(args.history, str) else None
                log_debug(f"Executing --history command (laptop_id: {laptop_id})", 'info')
                self.handle_history_command(laptop_id)
                return
        except Exception as e:
            log_debug(f"Error executing command: {e}", 'error')
            log_debug("Exception traceback:", 'exception')
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
            return
        
        # Identify laptop
        laptop_id = self.identify_laptop()
        print(f"\nCurrent Laptop: {laptop_id}")
        log_debug(f"Current laptop identified: {laptop_id}", 'info')
        
        # Check for existing data and show results if available
        if self.data_logger.data.get('laptops'):
            log_debug(f"Found existing test data for {len(self.data_logger.data['laptops'])} laptop(s)", 'info')
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
            log_debug(f"Incomplete test found: {incomplete_test}", 'info')
            if args.resume:
                log_debug("Resuming test automatically (--resume flag)", 'info')
                resume_data = self.test_resumer.resume_test(laptop_id)
            else:
                if self.test_resumer.prompt_resume(incomplete_test):
                    log_debug("User chose to resume test", 'info')
                    resume_data = self.test_resumer.resume_test(laptop_id)
                else:
                    log_debug("User chose not to resume, archiving incomplete test", 'info')
                    self.test_resumer.archive_incomplete_test(laptop_id)
        else:
            log_debug("No incomplete test found", 'info')
        
        # Run validation
        if args.validate:
            log_debug("Running validation only (--validate flag)", 'info')
            is_valid = self.run_validation(laptop_id, interactive=False)
            if not is_valid:
                print("\nValidation failed. Please fix errors and try again.")
            return
        
        if not resume_data and not self.skip_validation:
            log_debug("Running pre-test validation", 'info')
            if not self.run_validation(laptop_id, interactive=False):
                print("\n" + "=" * 70)
                print("VALIDATION FAILED")
                print("=" * 70)
                print("\nThe test cannot start due to validation errors.")
                print("Please fix the issues and try again.")
                print("\nTip: Use --skip-validation to bypass (not recommended)")
                return
        elif self.skip_validation:
            log_debug("Validation skipped (--skip-validation flag)", 'warning')
            print("\n⚠️  Warning: Validation skipped. Test may not be accurate.")
        
        # Start test
        try:
            log_debug(f"Starting test for laptop: {laptop_id}", 'info')
            if resume_data:
                log_debug(f"Resuming test with data: {resume_data}", 'info')
            self.start_test(laptop_id, resume_data, auto_start=args.auto_start)
        except KeyboardInterrupt:
            log_debug("Test interrupted by user (KeyboardInterrupt)", 'warning')
            print("\n\n⚠️  Test interrupted by user")
        except Exception as e:
            log_debug(f"Error during test: {e}", 'error')
            log_debug("Exception traceback:", 'exception')
            print(f"\n❌ Error during test: {e}")
            traceback.print_exc()


def _battery_bar(percent, width=20):
    """Terminal battery bar: ████░░░░░░"""
    filled = max(0, min(width, int(round(percent / 100 * width))))
    return '█' * filled + '░' * (width - filled)


def pause_before_exit():
    """Pause before exiting so user can see error messages"""
    if sys.platform == 'win32':
        try:
            input("\n\nPress Enter to exit...")
        except (KeyboardInterrupt, EOFError):
            time.sleep(5)
    else:
        try:
            input("\n\nPress Enter to exit...")
        except (KeyboardInterrupt, EOFError):
            pass


def show_main_menu():
    """Display interactive main menu"""
    print("\n" + "=" * 70)
    print("WINDOWS LAPTOP BATTERY TESTER")
    if DEBUG_MODE:
        print("  [DEBUG MODE ENABLED]")
        if debug_logger:
            # Get the log file path from the handler
            log_file = None
            for handler in debug_logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    log_file = handler.baseFilename
                    break
            if log_file:
                print(f"  Log: {os.path.basename(log_file)}")
    print("=" * 70)
    print("\nMain Menu:")
    print("  1. Start New Battery Test")
    print("  2. Auto-Start (wait for battery power)")
    print("  3. Quick Test (30 min estimate)")
    print("  4. Battery Calibration")
    print("  5. Resume Interrupted Test")
    print("  6. View Test Results")
    print("  7. Generate Report")
    print("  8. Run Validation Checks")
    print("  9. View All Laptops Summary")
    print("  0. Compare All Laptops")
    print("  C. Show Config")
    if DEBUG_MODE:
        print("  D. Disable Debug Mode")
        print("  X. Exit")
    else:
        print("  D. Enable Debug Mode")
        print("  X. Exit")
    print("\n" + "=" * 70)
    
    while True:
        try:
            choice = input("\nSelect an option: ").strip().lower()

            if choice == '1':
                return 'start_test'
            elif choice == '2':
                return 'auto_start'
            elif choice == '3':
                return 'quick_test'
            elif choice == '4':
                return 'calibration'
            elif choice == '5':
                return 'resume'
            elif choice == '6':
                return 'view_results'
            elif choice == '7':
                return 'report'
            elif choice == '8':
                return 'validate'
            elif choice == '9':
                return 'list'
            elif choice == '0':
                return 'compare'
            elif choice == 'c':
                return 'config'
            elif choice == 'd':
                return 'disable_debug' if DEBUG_MODE else 'enable_debug'
            elif choice == 'x':
                return 'exit'
            else:
                print("Invalid choice.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return 'exit'
        except EOFError:
            return 'exit'


def main():
    """Main entry point"""
    try:
        # Check for debug flag early
        if '--debug' in sys.argv:
            setup_debug_logging()
            log_debug("Application started", 'info')
            log_debug(f"Command line: {sys.argv}", 'debug')
        
        tester = BatteryTester()
        
        # Check if any command-line arguments were provided
        if len(sys.argv) > 1:
            log_debug("Running in command-line mode", 'info')
            # Run with command-line arguments (existing behavior)
            try:
                tester.run()
                log_debug("Command-line execution completed", 'info')
            except KeyboardInterrupt:
                log_debug("Operation cancelled by user", 'warning')
                print("\n\nOperation cancelled.")
            except Exception as e:
                log_debug(f"Error in command-line mode: {e}", 'error')
                log_debug("Exception traceback:", 'exception')
                print(f"\n❌ Error: {e}")
                traceback.print_exc()
            # For command-line mode, pause before exit
            pause_before_exit()
        else:
            log_debug("Running in interactive menu mode", 'info')
            # Show interactive menu
            while True:
                log_debug("Showing main menu", 'debug')
                choice = show_main_menu()
                log_debug(f"User selected menu option: {choice}", 'info')
                
                if choice == 'exit':
                    log_debug("User chose to exit", 'info')
                    print("\nGoodbye!")
                    pause_before_exit()
                    break
                elif choice == 'enable_debug':
                    if not DEBUG_MODE:
                        setup_debug_logging()
                        log_file = None
                        for handler in debug_logger.handlers:
                            if isinstance(handler, logging.FileHandler):
                                log_file = handler.baseFilename
                                break
                        print("\n" + "=" * 70)
                        print("✓ DEBUG MODE ENABLED")
                        print("=" * 70)
                        if log_file:
                            print(f"\nLog file: {os.path.abspath(log_file)}")
                        print("\nAll operations will now be logged to the file above.")
                        print("You can share this log file for troubleshooting.")
                        input("\nPress Enter to return to main menu...")
                    else:
                        print("\nDebug mode is already enabled.")
                        input("\nPress Enter to continue...")
                elif choice == 'disable_debug':
                    if DEBUG_MODE:
                        global debug_logger, DEBUG_MODE
                        log_file = None
                        if debug_logger:
                            for handler in debug_logger.handlers:
                                if isinstance(handler, logging.FileHandler):
                                    log_file = handler.baseFilename
                                    break
                            
                            # Close log file handlers
                            for handler in debug_logger.handlers[:]:
                                handler.close()
                                debug_logger.removeHandler(handler)
                        
                        # Reset globals
                        debug_logger = None
                        DEBUG_MODE = False
                        
                        log_debug("Debug mode disabled by user", 'info')  # This won't log since we just disabled it
                        
                        print("\n" + "=" * 70)
                        print("✓ DEBUG MODE DISABLED")
                        print("=" * 70)
                        if log_file:
                            print(f"\nLast log file: {os.path.basename(log_file)}")
                            print(f"Full path: {os.path.abspath(log_file)}")
                        print("\nDebug logging has been stopped.")
                        print("You can re-enable it anytime from the menu.")
                        input("\nPress Enter to return to main menu...")
                    else:
                        print("\nDebug mode is not enabled.")
                        input("\nPress Enter to continue...")
                elif choice == 'start_test':
                    log_debug("User selected: Start New Battery Test", 'info')
                    tester.selected_preset = None
                    try:
                        tester._run_start_test_interactive(auto_start=False)
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                elif choice == 'auto_start':
                    log_debug("User selected: Auto-Start", 'info')
                    tester.selected_preset = None
                    try:
                        tester._run_start_test_interactive(auto_start=True)
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                elif choice == 'quick_test':
                    log_debug("User selected: Quick Test", 'info')
                    tester.selected_preset = 'quick_test'
                    tester.low_battery_threshold = PRESETS['quick_test']['low_battery_threshold']
                    print(f"\nQuick Test: runs for 30 min, estimates full runtime from discharge rate.")
                    try:
                        tester._run_start_test_interactive()
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                elif choice == 'calibration':
                    log_debug("User selected: Battery Calibration", 'info')
                    tester.selected_preset = 'battery_calibration'
                    tester.low_battery_threshold = PRESETS['battery_calibration']['low_battery_threshold']
                    print(f"\nBattery Calibration: full discharge required. Connect AC when prompted.")
                    try:
                        tester._run_start_test_interactive()
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                elif choice == 'config':
                    tester.config.show()
                    try:
                        kv = input("\nSet config (KEY=VALUE) or Enter to return: ").strip()
                        if '=' in kv:
                            key, _, val = kv.partition('=')
                            key = key.strip()
                            val = val.strip()
                            if val.isdigit():
                                val = int(val)
                            elif val.lower() in ('true', 'false'):
                                val = val.lower() == 'true'
                            tester.config.set(key, val)
                            print(f"  ✓ {key} = {val}")
                    except (KeyboardInterrupt, EOFError):
                        pass
                    except KeyboardInterrupt:
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                elif choice == 'resume':
                    log_debug("User selected: Resume Interrupted Test", 'info')
                    try:
                        tester._run_resume_interactive()
                    except KeyboardInterrupt:
                        log_debug("Resume operation cancelled", 'warning')
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        log_debug(f"Error in resume: {e}", 'error')
                        log_debug("Exception traceback:", 'exception')
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                elif choice == 'view_results':
                    log_debug("User selected: View Test Results", 'info')
                    try:
                        tester._run_view_results_interactive()
                    except KeyboardInterrupt:
                        log_debug("View results operation cancelled", 'warning')
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        log_debug(f"Error viewing results: {e}", 'error')
                        log_debug("Exception traceback:", 'exception')
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                elif choice == 'report':
                    log_debug("User selected: Generate Report", 'info')
                    try:
                        tester._run_report_interactive()
                    except KeyboardInterrupt:
                        log_debug("Report generation cancelled", 'warning')
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        log_debug(f"Error generating report: {e}", 'error')
                        log_debug("Exception traceback:", 'exception')
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                elif choice == 'validate':
                    log_debug("User selected: Run Validation Checks", 'info')
                    try:
                        tester._run_validate_interactive()
                    except KeyboardInterrupt:
                        log_debug("Validation operation cancelled", 'warning')
                        print("\n\nOperation cancelled.")
                    except Exception as e:
                        log_debug(f"Error in validation: {e}", 'error')
                        log_debug("Exception traceback:", 'exception')
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                elif choice == 'list':
                    log_debug("User selected: View All Laptops Summary", 'info')
                    try:
                        tester.handle_list_command()
                    except Exception as e:
                        log_debug(f"Error listing laptops: {e}", 'error')
                        log_debug("Exception traceback:", 'exception')
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                elif choice == 'compare':
                    log_debug("User selected: Compare All Laptops", 'info')
                    try:
                        tester.handle_compare_command(sort_by='runtime')
                    except Exception as e:
                        log_debug(f"Error comparing laptops: {e}", 'error')
                        log_debug("Exception traceback:", 'exception')
                        print(f"\n❌ Error: {e}")
                        traceback.print_exc()
                    # Return to menu automatically
                
                # Automatically return to menu (except for exit)
                if choice != 'exit':
                    try:
                        input("\n\nPress Enter to return to main menu...")
                    except (KeyboardInterrupt, EOFError):
                        # If interrupted, ask if they want to exit
                        try:
                            exit_choice = input("\nExit? (y/n): ").strip().lower()
                            if exit_choice == 'y':
                                print("\nGoodbye!")
                                pause_before_exit()
                                break
                        except:
                            break
        
    except KeyboardInterrupt:
        log_debug("Application interrupted by user", 'warning')
        print("\n\nExiting...")
    except Exception as e:
        log_debug(f"Fatal error: {e}", 'critical')
        log_debug("Fatal exception traceback:", 'exception')
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        pause_before_exit()
        sys.exit(1)
    finally:
        if DEBUG_MODE:
            log_debug("Application shutting down", 'info')
            log_debug("=" * 70, 'info')


if __name__ == '__main__':
    main()

"""
Report Generator Module
Generate JPEG reports with battery stats and hardware info
"""
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

try:
    from data_logger import DataLogger
    from results_viewer import ResultsViewer
except ImportError:
    DataLogger = None
    ResultsViewer = None


class ReportGenerator:
    """Generate JPEG reports for battery tests"""
    
    def __init__(self, data_logger):
        if data_logger is None:
            raise ValueError("data_logger is required")
        self.data_logger = data_logger
        if ResultsViewer is None:
            raise ImportError("ResultsViewer not available")
        self.results_viewer = ResultsViewer(data_logger)
        self.width = 1920
        self.height = 1080
        self.margin = 50
        self.bg_color = (255, 255, 255)
        self.text_color = (0, 0, 0)
        self.accent_color = (0, 100, 200)
    
    def _get_font(self, size=20):
        """Get font, fallback to default if custom font not available"""
        try:
            # Try to use a system font
            if os.name == 'nt':  # Windows
                font_path = "C:/Windows/Fonts/arial.ttf"
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
        except:
            pass
        
        # Fallback to default font
        return ImageFont.load_default()
    
    def generate_report(self, laptop_id, run_id=None, output_path=None):
        """Generate JPEG report for a laptop/test run"""
        if laptop_id not in self.data_logger.data['laptops']:
            raise ValueError(f"Laptop {laptop_id} not found")
        
        laptop = self.data_logger.data['laptops'][laptop_id]
        test_runs = laptop['test_runs']
        
        # Find test run
        if run_id:
            test_run = next((tr for tr in test_runs if tr['run_id'] == run_id), None)
        else:
            # Use latest completed test run
            test_run = None
            for tr in reversed(test_runs):
                if tr['status'] in ['completed', 'low_battery_shutdown']:
                    test_run = tr
                    break
        
        if not test_run:
            raise ValueError("No completed test run found")
        
        # Create image
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fonts
        font_large = self._get_font(36)
        font_medium = self._get_font(24)
        font_small = self._get_font(18)
        font_tiny = self._get_font(14)
        
        y = self.margin
        
        # Title
        title = f"Battery Test Report - {laptop_id}"
        draw.text((self.margin, y), title, fill=self.accent_color, font=font_large)
        y += 60
        
        # Test run info
        run_info = f"Test Run: {test_run['run_id']} | Status: {test_run['status']}"
        draw.text((self.margin, y), run_info, fill=self.text_color, font=font_small)
        y += 40
        
        # Hardware Information
        hw = laptop['hardware_info']
        draw.text((self.margin, y), "Hardware Information", fill=self.accent_color, font=font_medium)
        y += 35
        
        hw_lines = [
            f"CPU: {hw.get('cpu', 'N/A')}",
            f"RAM: {hw.get('ram_gb', 'N/A')} GB",
            f"Model: {hw.get('system_model', 'N/A')}",
            f"Manufacturer: {hw.get('manufacturer', 'N/A')}",
        ]
        
        for line in hw_lines:
            draw.text((self.margin + 20, y), line, fill=self.text_color, font=font_small)
            y += 25
        
        y += 20
        
        # Battery Health
        if test_run.get('battery_info'):
            bat_info = test_run['battery_info']
            draw.text((self.margin, y), "Battery Health", fill=self.accent_color, font=font_medium)
            y += 35
            
            health_lines = []
            if bat_info.get('design_capacity_mwh'):
                health_lines.append(f"Design Capacity: {bat_info['design_capacity_mwh']:,} mWh")
            if bat_info.get('full_charge_capacity_mwh'):
                health_lines.append(f"Full Charge Capacity: {bat_info['full_charge_capacity_mwh']:,} mWh")
            if bat_info.get('health_percent'):
                health_lines.append(f"Health: {bat_info['health_percent']:.1f}%")
            
            for line in health_lines:
                draw.text((self.margin + 20, y), line, fill=self.text_color, font=font_small)
                y += 25
            
            y += 20
        
        # Test Statistics
        stats = self.results_viewer.get_test_statistics(test_run)
        if stats:
            draw.text((self.margin, y), "Test Statistics", fill=self.accent_color, font=font_medium)
            y += 35
            
            stat_lines = [
                f"Total Runtime: {stats['formatted_runtime']}",
                f"Discharge Rate: {stats['discharge_rate']:.2f}% per hour",
                f"Status: {stats['status']}",
            ]
            
            for line in stat_lines:
                draw.text((self.margin + 20, y), line, fill=self.text_color, font=font_small)
                y += 25
            
            # Milestones
            if stats['milestones']:
                y += 10
                draw.text((self.margin + 20, y), "Battery Milestones:", fill=self.text_color, font=font_small)
                y += 25
                
                milestone_x = self.margin + 40
                for pct in [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0]:
                    if pct in stats['milestones']:
                        milestone_text = f"{pct:3d}%: {stats['milestones'][pct]['formatted_time']}"
                        draw.text((milestone_x, y), milestone_text, fill=self.text_color, font=font_tiny)
                        y += 20
        
        # Test Metadata
        if test_run.get('test_metadata'):
            metadata = test_run['test_metadata']
            y += 20
            draw.text((self.margin, y), "Test Environment", fill=self.accent_color, font=font_medium)
            y += 35
            
            meta_lines = [
                f"OS: {metadata.get('os_version', 'N/A')}",
                f"Power Plan: {metadata.get('active_power_plan', 'N/A')}",
            ]
            
            if metadata.get('screen_brightness'):
                meta_lines.append(f"Screen Brightness: {metadata['screen_brightness']}%")
            
            for line in meta_lines:
                draw.text((self.margin + 20, y), line, fill=self.text_color, font=font_small)
                y += 25
        
        # Discharge Chart (simple bar chart)
        if test_run['entries']:
            y += 30
            chart_y = y
            chart_height = 200
            chart_width = self.width - (self.margin * 2)
            chart_x = self.margin
            
            # Draw chart background
            draw.rectangle(
                [(chart_x, chart_y), (chart_x + chart_width, chart_y + chart_height)],
                fill=(240, 240, 240),
                outline=self.text_color
            )
            
            # Draw discharge curve
            entries = test_run['entries']
            if len(entries) > 1:
                max_time = max(e['elapsed_seconds'] for e in entries)
                max_percent = 100
                
                points = []
                for entry in entries:
                    x = chart_x + int((entry['elapsed_seconds'] / max_time) * chart_width)
                    y_pos = chart_y + chart_height - int((entry['battery_percent'] / max_percent) * chart_height)
                    points.append((x, y_pos))
                
                # Draw line
                if len(points) > 1:
                    draw.line(points, fill=self.accent_color, width=3)
                
                # Draw axes labels
                draw.text((chart_x, chart_y + chart_height + 10), "0%", fill=self.text_color, font=font_tiny)
                draw.text((chart_x, chart_y - 20), "100%", fill=self.text_color, font=font_tiny)
                draw.text((chart_x + chart_width - 50, chart_y + chart_height + 10), 
                         self.results_viewer.format_time(max_time), fill=self.text_color, font=font_tiny)
            
            y += chart_height + 40
        
        # Footer
        footer_y = self.height - 50
        footer_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        draw.text((self.margin, footer_y), footer_text, fill=(128, 128, 128), font=font_tiny)
        
        # Save image
        if output_path is None:
            if run_id:
                output_path = f"battery_test_report_{laptop_id}_{run_id}.jpg"
            else:
                output_path = f"battery_test_report_{laptop_id}.jpg"
        
        img.save(output_path, 'JPEG', quality=95)
        return output_path
    
    def generate_report_and_open(self, laptop_id, run_id=None, output_path=None, auto_open=True):
        """Generate report and optionally open it"""
        report_path = self.generate_report(laptop_id, run_id, output_path)
        
        if auto_open:
            try:
                import os
                import platform
                if platform.system() == 'Windows':
                    os.startfile(report_path)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{report_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{report_path}"')
            except Exception as e:
                print(f"Warning: Could not open report: {e}")
        
        return report_path
    
    def generate_comparison_report(self, output_path=None):
        """Generate comparison report for all laptops"""
        laptops = self.data_logger.data['laptops']
        
        if not laptops:
            raise ValueError("No laptops found")
        
        # Create image
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fonts
        font_large = self._get_font(36)
        font_medium = self._get_font(24)
        font_small = self._get_font(18)
        
        y = self.margin
        
        # Title
        title = "Battery Test Comparison Report"
        draw.text((self.margin, y), title, fill=self.accent_color, font=font_large)
        y += 60
        
        # Collect data for all laptops
        laptop_data = []
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
                stats = self.results_viewer.get_test_statistics(latest_run)
                if stats:
                    laptop_data.append({
                        'laptop_id': laptop_id,
                        'hardware': laptop['hardware_info'],
                        'stats': stats,
                    })
        
        # Display comparison table
        table_y = y + 20
        draw.text((self.margin, y), "Laptop Comparison", fill=self.accent_color, font=font_medium)
        y = table_y + 40
        
        # Table header
        headers = ["Laptop ID", "Runtime", "Discharge Rate", "Status"]
        col_widths = [300, 150, 150, 150]
        x = self.margin
        
        for i, header in enumerate(headers):
            draw.text((x, y), header, fill=self.accent_color, font=font_small)
            x += col_widths[i]
        
        y += 30
        
        # Table rows
        for item in laptop_data[:10]:  # Limit to 10 laptops
            x = self.margin
            draw.text((x, y), item['laptop_id'][:25], fill=self.text_color, font=font_small)
            x += col_widths[0]
            
            draw.text((x, y), item['stats']['formatted_runtime'], fill=self.text_color, font=font_small)
            x += col_widths[1]
            
            discharge_text = f"{item['stats']['discharge_rate']:.2f}%/hr"
            draw.text((x, y), discharge_text, fill=self.text_color, font=font_small)
            x += col_widths[2]
            
            draw.text((x, y), item['stats']['status'], fill=self.text_color, font=font_small)
            
            y += 30
        
        # Footer
        footer_y = self.height - 50
        footer_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        draw.text((self.margin, footer_y), footer_text, fill=(128, 128, 128), font=self._get_font(14))
        
        # Save image
        if output_path is None:
            output_path = "battery_test_comparison.jpg"
        
        img.save(output_path, 'JPEG', quality=95)
        return output_path


if __name__ == '__main__':
    from data_logger import DataLogger
    
    logger = DataLogger('test_data.json')
    generator = ReportGenerator(logger)
    
    print("Report Generator Test:")
    print("=" * 50)
    
    # Try to generate a report (will fail if no data)
    try:
        laptops = list(logger.data['laptops'].keys())
        if laptops:
            report_path = generator.generate_report(laptops[0])
            print(f"Report generated: {report_path}")
        else:
            print("No laptops found in data")
    except Exception as e:
        print(f"Error generating report: {e}")

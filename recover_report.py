#!/usr/bin/env python3
"""
Generate PenDoc report from existing screenshots (recovery tool)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.report_builder import ReportBuilder
from lib.command_generator import CommandGenerator
from lib.enrichment import EnrichmentEngine

def load_config():
    """Load PenDoc configuration"""
    config_path = Path('config/pendoc.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def scan_existing_screenshots(output_dir: Path) -> list:
    """Scan output directory for existing screenshots"""
    results = []
    screenshots_dir = output_dir / 'screenshots'
    
    if not screenshots_dir.exists():
        print(f"❌ Error: Screenshots directory not found: {screenshots_dir}")
        return []
    
    print(f"📁 Scanning: {screenshots_dir}")
    
    # Look for all screenshot files recursively (they're in subdirectories by domain)
    for screenshot_file in sorted(screenshots_dir.rglob('*.png')):
        # Extract domain from parent directory name
        domain = screenshot_file.parent.name
        
        # Create result entry
        result = {
            'url': f"https://{domain}",
            'status': 'success',
            'screenshot': str(screenshot_file.relative_to(screenshots_dir)),
            'timestamp': datetime.fromtimestamp(screenshot_file.stat().st_mtime).isoformat(),
            'domain': domain,
            'source': 'recovered_screenshot',
            'http_headers': {},
            'technologies': []
        }
        results.append(result)
    
    print(f"✅ Found {len(results)} existing screenshots\n")
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 recover_report.py <output_directory>")
        print("\nExample:")
        print("  python3 recover_report.py pendocqk")
        print("\nThis will generate reports from existing screenshots without re-scanning.")
        sys.exit(1)
    
    output_path = Path(sys.argv[1])
    
    if not output_path.exists():
        print(f"❌ Error: Output directory does not exist: {output_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("  PenDoc Recovery - Generate Report from Existing Screenshots")
    print("=" * 60)
    print()
    
    # Load config
    config = load_config()
    
    # Scan for existing screenshots
    results = scan_existing_screenshots(output_path)
    
    if not results:
        print("❌ No screenshots found!")
        sys.exit(1)
    
    # Try to enrich with metadata (optional)
    print("📊 Enriching metadata...")
    try:
        enrichment_engine = EnrichmentEngine(config)
        results = enrichment_engine.enrich_all(results)
        print("✅ Metadata enrichment complete\n")
    except Exception as e:
        print(f"⚠️  Metadata enrichment failed (non-fatal): {e}\n")
    
    # Generate report
    print("📄 Generating HTML report...")
    report_builder = ReportBuilder(config, output_path)
    report_path = report_builder.generate(results)
    print(f"✅ Report generated: {report_path}\n")
    
    # Generate command files
    print("🔧 Generating pen testing command files...")
    command_generator = CommandGenerator(output_path)
    command_files = command_generator.generate_all(results)
    print(f"✅ Command files generated\n")
    
    # Summary
    print("=" * 60)
    print("  Recovery Summary")
    print("=" * 60)
    print(f"  Recovered screenshots: {len(results)}")
    print(f"  Report: {report_path}")
    
    if command_files:
        print(f"\n  Generated command files:")
        for tool, path in command_files.items():
            print(f"    • {tool}: {Path(path).name}")
    
    print("=" * 60)
    print("\n✨ Recovery complete! Your report is ready.\n")

if __name__ == '__main__':
    main()


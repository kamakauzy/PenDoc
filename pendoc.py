#!/usr/bin/env python3
"""
PenDoc - Penetration Testing Documentation Tool
Automated screenshot and metadata capture for pen testing documentation
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import yaml
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

from lib.screenshot import ScreenshotEngine
from lib.enrichment import EnrichmentEngine
from lib.report_builder import ReportBuilder
from lib.command_generator import CommandGenerator
from lib.input_parsers.url_parser import URLParser
from lib.input_parsers.burp_parser import BurpParser
from lib.input_parsers.subdomain_parser import SubdomainParser
from lib.input_parsers.nmap_parser import NmapParser


class PenDoc:
    """Main PenDoc application class"""
    
    def __init__(self, config_path: str = "config/pendoc.yaml"):
        """Initialize PenDoc with configuration"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"{Fore.YELLOW}Warning: Config file not found, using defaults{Style.RESET_ALL}")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            'screenshots': {
                'viewports': {'desktop': {'width': 1920, 'height': 1080}},
                'capture_desktop': True,
                'full_page': True,
                'timeout': 30,
                'wait_after_load': 2000
            },
            'performance': {
                'concurrent_workers': 5,
                'max_retries': 2,
                'retry_delay': 5
            },
            'http': {
                'follow_redirects': True,
                'verify_ssl': False,
                'user_agent': 'Mozilla/5.0 PenDoc/1.0'
            },
            'input': {
                'default_protocol': 'https',
                'http_ports': [80, 8000, 8080, 8888],
                'https_ports': [443, 8443, 9443]
            },
            'enrichment': {
                'collect_headers': True,
                'detect_technologies': True,
                'collect_ssl_info': True
            },
            'report': {
                'title': 'PenDoc Report',
                'group_by_domain': True,
                'show_metadata': True,
                'theme': 'dark'
            },
            'logging': {
                'level': 'INFO',
                'show_progress': True
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['logging']['level'])
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.StreamHandler()]
        )
    
    def parse_inputs(self, args: argparse.Namespace) -> list:
        """Parse all input sources and return unified target list"""
        targets = []
        
        # Parse URL list
        if args.urls:
            self.logger.info(f"Parsing URL list from {args.urls}")
            parser = URLParser(self.config)
            targets.extend(parser.parse(args.urls))
        
        # Parse Burp Suite sitemap
        if args.burp:
            self.logger.info(f"Parsing Burp Suite sitemap from {args.burp}")
            parser = BurpParser(self.config)
            targets.extend(parser.parse(args.burp))
        
        # Parse subdomain list
        if args.subdomains:
            self.logger.info(f"Parsing subdomain list from {args.subdomains}")
            parser = SubdomainParser(self.config)
            targets.extend(parser.parse(args.subdomains))
        
        # Parse Nmap results
        if args.nmap:
            self.logger.info(f"Parsing Nmap scan from {args.nmap}")
            parser = NmapParser(self.config)
            targets.extend(parser.parse(args.nmap))
        
        # Remove duplicates while preserving order
        unique_targets = []
        seen = set()
        for target in targets:
            if target['url'] not in seen:
                unique_targets.append(target)
                seen.add(target['url'])
        
        self.logger.info(f"Total unique targets: {len(unique_targets)}")
        return unique_targets
    
    def run(self, args: argparse.Namespace):
        """Main execution flow"""
        start_time = datetime.now()
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"  PenDoc - Penetration Testing Documentation Tool")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Parse inputs
        targets = self.parse_inputs(args)
        
        if not targets:
            print(f"{Fore.RED}Error: No targets found from input sources{Style.RESET_ALL}")
            sys.exit(1)
        
        print(f"{Fore.GREEN}✓ Loaded {len(targets)} targets{Style.RESET_ALL}\n")
        
        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize engines
        screenshot_engine = ScreenshotEngine(self.config, output_dir)
        enrichment_engine = EnrichmentEngine(self.config)
        
        # Process targets
        print(f"{Fore.CYAN}Starting screenshot capture...{Style.RESET_ALL}\n")
        results = screenshot_engine.capture_all(targets)
        
        # Enrich with metadata
        if self.config['enrichment']['collect_headers']:
            print(f"\n{Fore.CYAN}Collecting metadata...{Style.RESET_ALL}\n")
            results = enrichment_engine.enrich_all(results)
        
        # Generate report
        print(f"\n{Fore.CYAN}Generating HTML report...{Style.RESET_ALL}\n")
        report_builder = ReportBuilder(self.config, output_dir)
        report_path = report_builder.generate(results)
        
        # Generate command files for downstream testing
        print(f"\n{Fore.CYAN}Generating pen testing command files...{Style.RESET_ALL}\n")
        command_generator = CommandGenerator(output_dir)
        command_files = command_generator.generate_all(results)
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'failed'])
        
        # Count detected CMSs
        cms_counts = {}
        for r in results:
            if r.get('status') == 'success':
                for tech in r.get('detected_technologies', []):
                    tech_name = tech['name'] if isinstance(tech, dict) else str(tech).lower()
                    if tech_name in ['wordpress', 'woocommerce', 'joomla', 'drupal', 'sharepoint', 
                                    'magento', 'prestashop', 'opencart', 'typo3', 'concrete5', 
                                    'umbraco', 'dotnetnuke', 'ghost', 'vbulletin', 'phpbb', 
                                    'mybb', 'discourse', 'confluence', 'mediawiki']:
                        cms_counts[tech_name] = cms_counts.get(tech_name, 0) + 1
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"  Summary")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"  Total targets: {len(targets)}")
        print(f"  {Fore.GREEN}Successful: {successful}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Failed: {failed}{Style.RESET_ALL}")
        
        if cms_counts:
            print(f"\n  {Fore.YELLOW}Detected CMSs:{Style.RESET_ALL}")
            for cms, count in sorted(cms_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"    {cms.title()}: {count}")
        
        print(f"\n  Duration: {duration:.2f}s")
        print(f"\n  Report: {Fore.YELLOW}{report_path}{Style.RESET_ALL}")
        
        if command_files:
            print(f"\n  {Fore.GREEN}Generated command files:{Style.RESET_ALL}")
            for tool, path in command_files.items():
                print(f"    {tool}: {path}")
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PenDoc - Automated penetration testing documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pendoc.py --urls urls.txt --output ./results
  pendoc.py --burp sitemap.xml --output ./results
  pendoc.py --subdomains subs.txt --output ./results
  pendoc.py --nmap scan.xml --output ./results
  pendoc.py --urls urls.txt --burp sitemap.xml --output ./results
        """
    )
    
    # Input sources
    parser.add_argument('--urls', help='File containing list of URLs')
    parser.add_argument('--burp', help='Burp Suite sitemap XML file')
    parser.add_argument('--subdomains', help='File containing list of subdomains')
    parser.add_argument('--nmap', help='Nmap XML scan results')
    
    # Output
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory (default: output)')
    
    # Configuration
    parser.add_argument('--config', '-c', default='config/pendoc.yaml',
                       help='Configuration file (default: config/pendoc.yaml)')
    
    args = parser.parse_args()
    
    # Validate at least one input source
    if not any([args.urls, args.burp, args.subdomains, args.nmap]):
        parser.error("At least one input source is required (--urls, --burp, --subdomains, or --nmap)")
    
    # Run PenDoc
    try:
        pendoc = PenDoc(config_path=args.config)
        pendoc.run(args)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Basic test script for PenDoc
Validates that all components are working
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        import yaml
        print("  ✓ PyYAML")
    except ImportError:
        print("  ✗ PyYAML not installed")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        print("  ✓ Playwright")
    except ImportError:
        print("  ✗ Playwright not installed")
        return False
    
    try:
        import requests
        print("  ✓ Requests")
    except ImportError:
        print("  ✗ Requests not installed")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("  ✓ BeautifulSoup4")
    except ImportError:
        print("  ✗ BeautifulSoup4 not installed")
        return False
    
    try:
        from jinja2 import Template
        print("  ✓ Jinja2")
    except ImportError:
        print("  ✗ Jinja2 not installed")
        return False
    
    try:
        from tqdm import tqdm
        print("  ✓ tqdm")
    except ImportError:
        print("  ✗ tqdm not installed")
        return False
    
    return True

def test_parsers():
    """Test that all parsers can be imported"""
    print("\nTesting parsers...")
    
    try:
        from lib.input_parsers.url_parser import URLParser
        print("  ✓ URLParser")
    except ImportError as e:
        print(f"  ✗ URLParser: {e}")
        return False
    
    try:
        from lib.input_parsers.burp_parser import BurpParser
        print("  ✓ BurpParser")
    except ImportError as e:
        print(f"  ✗ BurpParser: {e}")
        return False
    
    try:
        from lib.input_parsers.subdomain_parser import SubdomainParser
        print("  ✓ SubdomainParser")
    except ImportError as e:
        print(f"  ✗ SubdomainParser: {e}")
        return False
    
    try:
        from lib.input_parsers.nmap_parser import NmapParser
        print("  ✓ NmapParser")
    except ImportError as e:
        print(f"  ✗ NmapParser: {e}")
        return False
    
    return True

def test_engines():
    """Test that core engines can be imported"""
    print("\nTesting engines...")
    
    try:
        from lib.screenshot import ScreenshotEngine
        print("  ✓ ScreenshotEngine")
    except ImportError as e:
        print(f"  ✗ ScreenshotEngine: {e}")
        return False
    
    try:
        from lib.enrichment import EnrichmentEngine
        print("  ✓ EnrichmentEngine")
    except ImportError as e:
        print(f"  ✗ EnrichmentEngine: {e}")
        return False
    
    try:
        from lib.report_builder import ReportBuilder
        print("  ✓ ReportBuilder")
    except ImportError as e:
        print(f"  ✗ ReportBuilder: {e}")
        return False
    
    return True

def test_examples():
    """Test that example files exist"""
    print("\nTesting example files...")
    
    examples = [
        'examples/urls.txt',
        'examples/subdomains.txt',
        'examples/burp_sitemap_example.xml',
        'examples/nmap_example.xml',
        'examples/README.md'
    ]
    
    all_exist = True
    for example in examples:
        if Path(example).exists():
            print(f"  ✓ {example}")
        else:
            print(f"  ✗ {example} not found")
            all_exist = False
    
    return all_exist

def test_config():
    """Test that config file exists and is valid"""
    print("\nTesting configuration...")
    
    config_path = Path('config/pendoc.yaml')
    
    if not config_path.exists():
        print("  ✗ config/pendoc.yaml not found")
        return False
    
    print("  ✓ config/pendoc.yaml exists")
    
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        print("  ✓ config/pendoc.yaml is valid YAML")
        
        # Check required sections
        required_sections = ['screenshots', 'performance', 'http', 'input', 'enrichment', 'report', 'logging']
        for section in required_sections:
            if section in config:
                print(f"  ✓ Section '{section}' present")
            else:
                print(f"  ✗ Section '{section}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading config: {e}")
        return False

def test_playwright_browsers():
    """Test if Playwright browsers are installed"""
    print("\nTesting Playwright browsers...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("  ✓ Chromium browser installed")
                return True
            except Exception as e:
                print(f"  ✗ Chromium not installed: {e}")
                print("  → Run: playwright install chromium")
                return False
    except Exception as e:
        print(f"  ✗ Error testing Playwright: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("PenDoc - Component Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Dependencies", test_imports()))
    results.append(("Parsers", test_parsers()))
    results.append(("Engines", test_engines()))
    results.append(("Examples", test_examples()))
    results.append(("Configuration", test_config()))
    results.append(("Playwright Browsers", test_playwright_browsers()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! PenDoc is ready to use.")
        print("\nTry running:")
        print("  python pendoc.py --urls examples/urls.txt --output test_output")
        return 0
    else:
        print("\n✗ Some tests failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")
        return 1

if __name__ == '__main__':
    sys.exit(main())


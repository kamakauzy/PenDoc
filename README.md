# PenDoc

**Automated penetration testing documentation tool for capturing screenshots and metadata from web applications**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Internal-green.svg)](LICENSE)

## Overview

PenDoc is a fully automated tool designed to streamline penetration testing documentation by capturing screenshots and metadata from web applications. It addresses the tedious and time-consuming task of manually documenting hundreds of web targets during security assessments.

**Problem it solves:**
- Manual screenshot capture is slow and inconsistent
- Processing hundreds of targets takes hours
- Creating organized reports requires significant effort
- Visual documentation is essential for pen test reports

**PenDoc automates all of this.**

## Features

- 📸 **Automated Screenshots**: Full-page screenshots with configurable viewports
- 🔌 **Multiple Input Sources**: Burp Suite, Nmap, subdomain enumeration, URL lists
- 🔍 **Metadata Enrichment**: HTTP headers, status codes, technology detection, SSL analysis
- 📊 **HTML Reports**: Modern, searchable, filterable gallery with dark mode
- ⚡ **Concurrent Processing**: Fast parallel capture with progress tracking
- 📱 **Multiple Viewports**: Desktop (default), tablet, and mobile screenshots
- 🎯 **Smart Filtering**: Exclude static resources, pattern-based filtering
- 🔒 **SSL Analysis**: Certificate information and expiration checking

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/kamakauzy/PenDoc.git
cd PenDoc

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Basic Usage

```bash
# From URL list
python pendoc.py --urls urls.txt --output ./results

# From Burp Suite sitemap
python pendoc.py --burp sitemap.xml --output ./results

# From subdomain enumeration
python pendoc.py --subdomains subdomains.txt --output ./results

# From Nmap scan
python pendoc.py --nmap scan.xml --output ./results

# Combine multiple sources
python pendoc.py --urls urls.txt --burp sitemap.xml --subdomains subs.txt --output ./results
```

### Quick Test

```bash
# Windows
quicktest.bat

# Manual test
python test_pendoc.py
python pendoc.py --urls examples/urls.txt --output test_output
```

## Architecture

### Technology Stack
- **Language**: Python 3.10+
- **Browser Automation**: Playwright (Chromium)
- **Report Generation**: Jinja2 templates
- **Configuration**: YAML
- **Async Processing**: asyncio for concurrent capture

### Core Components

```
PenDoc/
├── pendoc.py                    # Main CLI application
├── lib/
│   ├── input_parsers/           # Modular input processing
│   │   ├── url_parser.py       # Simple URL lists
│   │   ├── burp_parser.py      # Burp Suite sitemap XML
│   │   ├── subdomain_parser.py # Subdomain enumeration
│   │   └── nmap_parser.py      # Nmap XML port scans
│   ├── screenshot.py            # Playwright capture engine
│   ├── enrichment.py            # Metadata collection
│   └── report_builder.py        # HTML report generation
├── config/
│   └── pendoc.yaml              # Configuration file
└── examples/                     # Sample input files
```

## Input Formats

### 1. URL Lists (--urls)
Simple text file with one URL per line:
```
https://example.com
https://admin.example.com/login
http://192.168.1.100:8080
# Comments are supported
```

### 2. Burp Suite Sitemap (--burp)
Export from Burp Suite:
1. Target → Site map
2. Right-click → "Save selected items"
3. Save as XML

### 3. Subdomain Lists (--subdomains)
Supports multiple formats:
- **Plain text**: One subdomain per line
- **CSV**: Domain in first column
- **JSON**: Array or objects with 'domain' field

```
www.example.com
admin.example.com
api.example.com
```

### 4. Nmap XML (--nmap)
XML output from Nmap port scans:
```bash
nmap -p- -sV -oX scan.xml target.com
python pendoc.py --nmap scan.xml --output results/
```

## Output

### Directory Structure
```
output/
├── index.html                    # Interactive HTML report
├── screenshots/
│   ├── example.com/
│   │   └── desktop/
│   │       ├── index_20251120_153000.png
│   │       └── admin_20251120_153005.png
│   └── admin.example.com/
│       └── desktop/
│           └── login_20251120_153010.png
└── metadata/
    └── results.json              # Raw JSON data
```

### HTML Report Features
- Modern, responsive design with dark/light mode
- Searchable and filterable by URL and status
- Click-to-zoom screenshots
- Grouped by domain
- Statistics dashboard (success rate, status codes, technologies)
- Metadata display (page titles, HTTP status, technologies)

## Configuration

Edit `config/pendoc.yaml` to customize:

### Screenshots
```yaml
screenshots:
  viewports:
    desktop: { width: 1920, height: 1080 }
    tablet: { width: 768, height: 1024 }
    mobile: { width: 375, height: 667 }
  capture_desktop: true      # Enable/disable viewports
  capture_tablet: false
  capture_mobile: false
  full_page: true            # Full-page vs viewport only
  timeout: 30                # Page load timeout (seconds)
  wait_after_load: 2000      # Wait for JS rendering (ms)
```

### Performance
```yaml
performance:
  concurrent_workers: 5      # Parallel screenshot captures
  max_retries: 2            # Retry failed captures
  retry_delay: 5            # Delay between retries (seconds)
```

### HTTP Settings
```yaml
http:
  follow_redirects: true
  verify_ssl: false          # Disable SSL verification (pen testing)
  user_agent: "Mozilla/5.0 ... PenDoc/1.0"
  headers: {}               # Custom HTTP headers
```

### Input Processing
```yaml
input:
  default_protocol: "https"
  http_ports: [80, 8000, 8080, 8888, 3000, 5000]
  https_ports: [443, 8443, 9443]
  exclude_patterns:         # Skip static resources
    - ".*\\.js$"
    - ".*\\.css$"
    - ".*\\.jpg$"
    - ".*\\.png$"
```

### Enrichment
```yaml
enrichment:
  collect_headers: true      # HTTP response headers
  detect_technologies: true  # Web servers, frameworks, WAF/CDN
  collect_ssl_info: true     # SSL certificate details
  interesting_headers:       # Headers to highlight
    - "Server"
    - "X-Powered-By"
    - "Content-Security-Policy"
```

### Report Settings
```yaml
report:
  title: "PenDoc - Penetration Testing Documentation"
  group_by_domain: true
  show_metadata: true
  theme: "dark"              # "dark" or "light"
```

## Advanced Features

### Metadata Enrichment
- **HTTP Information**: Status codes, headers, response timing, page titles
- **Security Headers**: Server, X-Powered-By, CSP, X-Frame-Options, HSTS
- **Technology Detection**: Web servers (Nginx, Apache, IIS), frameworks (PHP, ASP.NET, Express.js), CDN/WAF (Cloudflare, Sucuri)
- **SSL/TLS Analysis**: Certificate information, issuer, validity period, expiration checking

### Error Handling
- Graceful timeout handling
- Automatic retry mechanism for transient failures
- Detailed error messages in report
- Continues processing on individual failures

### Extensibility
- Modular parser architecture (easy to add new input formats)
- YAML-based configuration
- Plugin-ready design
- JSON export for automation

## Use Cases

### 1. Reconnaissance Documentation
- Screenshot all discovered subdomains
- Visual inventory of target infrastructure
- Identify interesting pages and applications
- Create baseline for comparison

### 2. Penetration Test Reports
- Document application interfaces
- Capture before/after exploitation
- Show proof of access
- Visual evidence for findings

### 3. Scope Verification
- Confirm target URLs are accessible
- Verify correct applications
- Identify out-of-scope resources
- Document testing boundaries

### 4. Workflow Integration
```bash
# Subdomain enumeration → PenDoc
subfinder -d example.com -o subdomains.txt
python pendoc.py --subdomains subdomains.txt --output recon/

# Port scanning → PenDoc
nmap -iL targets.txt -p- -sV -oX scan.xml
python pendoc.py --nmap scan.xml --output portscan/

# Burp Suite testing → PenDoc
# (Export sitemap from Burp)
python pendoc.py --burp sitemap.xml --output manual_test/
```

### 5. Integration with Cronos Platform
```python
from database import db_util

# Export web hosts from Cronos
hosts = db_util.get_web_hosts(client_id='ABC123')

# Create input for PenDoc
with open('urls.txt', 'w') as f:
    for host in hosts:
        f.write(f"{host['url']}\n")

# Run PenDoc
import subprocess
subprocess.run([
    'python', 'pendoc.py',
    '--urls', 'urls.txt',
    '--output', f'output/{client_id}_screenshots'
])
```

## Performance

- **Speed**: ~5-10 targets/minute (depends on site response time)
- **Concurrency**: 5 parallel workers (configurable up to 20+)
- **Memory**: ~500MB-2GB (scales with concurrency)
- **Network**: Efficient, reuses browser context

### Optimization Tips

1. **Concurrent Workers**: Start with 5, increase based on:
   - Network bandwidth
   - Target responsiveness
   - Available system resources

2. **Timeout Values**:
   - Fast networks: 15-20s
   - Slow targets: 30-60s
   - Very slow: 60-120s

3. **Viewport Selection**:
   - Desktop only: Fastest (default)
   - All viewports: 3x slower but most complete

4. **Resource Filtering**:
   - Use `exclude_patterns` for static files
   - Reduces unnecessary captures
   - Speeds up processing

5. **Batch Processing**:
   - Split large target lists
   - Run multiple instances for very large scans

## Common Issues

### Playwright not found
```bash
playwright install chromium
```

### SSL certificate errors
Set `verify_ssl: false` in `config/pendoc.yaml`

### Timeouts on slow sites
Increase `timeout` value in `config/pendoc.yaml`

### Out of memory
Reduce `concurrent_workers` in `config/pendoc.yaml`

### Import errors
```bash
pip install -r requirements.txt
```

## Testing

Run the included test suite to validate installation:

```bash
python test_pendoc.py
```

This validates:
- ✓ All dependencies installed
- ✓ All modules importable
- ✓ Example files present
- ✓ Configuration valid
- ✓ Playwright browsers installed

## Examples

The `examples/` directory contains sample input files:
- `urls.txt` - Sample URL list
- `subdomains.txt` - Sample subdomain list
- `burp_sitemap_example.xml` - Sample Burp Suite export
- `nmap_example.xml` - Sample Nmap scan

## Future Enhancements

### Planned Features
- Authentication support (credentials, cookies, API tokens)
- JavaScript interaction (click buttons, fill forms)
- Comparison mode (diff screenshots over time)
- Advanced analysis (response body inspection, vulnerability patterns)
- Additional outputs (PDF reports, CSV exports)
- Masscan support

### Current Limitations
- No authentication support (yet)
- No JavaScript interaction beyond page load
- No custom cookies/sessions
- Single viewport per run (but configurable)

## Security Considerations

- ✅ No credential storage
- ✅ Local execution only
- ✅ Sanitized file paths (no traversal)
- ✅ SSL verification configurable
- ✅ No remote code execution
- ✅ Safe for production use in pen testing context

## Requirements

- Python 3.10 or higher
- Playwright (Chromium browser)
- 2GB RAM minimum (more for concurrent workers)
- Network access to targets

## License

Internal tool for penetration testing use.

## Contributing

Feedback and contributions welcome! Feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Share integration examples

## Credits

Built with focus on:
- **Modularity**: Easy to extend with new input parsers
- **Performance**: Concurrent processing for speed
- **Usability**: Clear output and good UX
- **Integration**: Works seamlessly with existing tools

## Quick Reference

```bash
# Installation
pip install -r requirements.txt && playwright install chromium

# Basic usage
python pendoc.py --urls urls.txt -o output/

# Multiple sources
python pendoc.py --urls u.txt --burp b.xml --subdomains s.txt --nmap n.xml -o out/

# Custom config
python pendoc.py --urls urls.txt -c custom.yaml -o output/

# Test installation
python test_pendoc.py

# Quick demo (Windows)
quicktest.bat
```

---

**Status**: ✅ Production-ready

For detailed feature documentation and advanced usage, see the inline comments in `config/pendoc.yaml` and the example files in `examples/`.

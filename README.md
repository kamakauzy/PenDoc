# PenDoc

![PenDoc Banner](20ea59b5-c9ff-4ebe-986b-55f1ac81e79c.png)

**Because manually screenshotting 500 web apps is NOT how you want to spend your Friday.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Internal-green.svg)](LICENSE)

## What Is This?

PenDoc is your automated screenshot slave for penetration testing. It captures screenshots and metadata from web applications so you don't have to manually document every single target like it's 2005.

**The Problem:**
- Manually screenshotting 500 targets? That's 8 hours of your life you're not getting back.
- Your report needs visual evidence but you'd rather be, you know, actually hacking things.
- Burp Suite doesn't automatically organize screenshots by domain because... reasons.
- Your pen test report looks like garbage without screenshots, but taking them is soul-crushing.

**The Solution:**
Point PenDoc at your targets, go grab coffee (or three), come back to organized screenshots and a pretty HTML report. You're welcome.

## Features

**Automated Screenshots**: Full-page screenshots because half a screenshot is useless

**Multiple Input Sources**: Burp Suite, Nmap, subdomain lists, or just a plain old URL list. We don't judge your workflow.

**Metadata Enrichment**: HTTP headers, status codes, tech detection, SSL analysis - all the metadata you forgot to document manually

**HTML Reports**: Modern, searchable gallery with dark mode (because pen testers don't use light mode, let's be real)

**Concurrent Processing**: Parallel capture with progress bars because watching paint dry is boring

**Multiple Viewports**: Desktop (default), tablet, and mobile if you hate yourself enough to enable them

**Smart Filtering**: Excludes .js, .css, .jpg, and other garbage you don't want screenshots of

**SSL Analysis**: Certificate details because someone on your team will ask "is the cert valid?" and you'll look prepared

## Installation (It's Not Rocket Surgery)

```bash
# Clone this bad boy
git clone https://github.com/kamakauzy/PenDoc.git
cd PenDoc

# Install Python stuff
pip install -r requirements.txt

# Install Playwright browsers (yes, this downloads Chromium, deal with it)
playwright install chromium
```

## Usage (The Easy Part)

```bash
# Got a URL list? Cool.
python pendoc.py --urls urls.txt --output ./results

# Burp Suite sitemap? Obviously.
python pendoc.py --burp sitemap.xml --output ./results

# Subdomain enumeration results? Hell yeah.
python pendoc.py --subdomains subdomains.txt --output ./results

# Nmap scan? We got you.
python pendoc.py --nmap scan.xml --output ./results

# Why choose one when you can use ALL THE INPUTS?
python pendoc.py --urls urls.txt --burp sitemap.xml --subdomains subs.txt --nmap scan.xml --output ./results
```

## Quick Test (Prove It Works)

```bash
# Windows users
quicktest.bat

# Or if you like typing
python test_pendoc.py
python pendoc.py --urls examples/urls.txt --output test_output
```

## How It Works (For The Curious)

### Technology Stack
- **Python 3.10+**: Because we're not animals using Python 2
- **Playwright**: Chromium automation that actually works
- **Jinja2**: HTML templating because string concatenation is for masochists
- **YAML**: Configuration that humans can read
- **asyncio**: Concurrent processing because your time is valuable

### Architecture (If You Care)

```
PenDoc/
├── pendoc.py                    # The main event
├── lib/
│   ├── input_parsers/           # Parsers for all your weird input formats
│   │   ├── url_parser.py       # Plain text URLs (exciting!)
│   │   ├── burp_parser.py      # Burp Suite XML (less exciting!)
│   │   ├── subdomain_parser.py # Subdomain lists (very exciting!)
│   │   └── nmap_parser.py      # Nmap XML (moderately exciting!)
│   ├── screenshot.py            # Where the magic happens
│   ├── enrichment.py            # Makes your data look fancy
│   └── report_builder.py        # HTML report generation
├── config/
│   └── pendoc.yaml              # Tweak all the knobs
└── examples/                     # Sample files so you can't screw up
```

## Input Formats (We Support Everything)

### URL Lists (--urls)
One URL per line. Comments work too. We're not monsters.
```
https://example.com
https://admin.example.com/login
http://192.168.1.100:8080
# This is a comment, genius
```

### Burp Suite Sitemap (--burp)
1. Target → Site map
2. Right-click → "Save selected items"
3. Save as XML
4. Point PenDoc at it

### Subdomain Lists (--subdomains)
We support everything because we love you:
- Plain text (one per line)
- CSV (domain in first column)
- JSON (array or objects with 'domain' field)

```
www.example.com
admin.example.com
api.example.com
```

### Nmap XML (--nmap)
Run Nmap with XML output, feed it to PenDoc, profit.
```bash
nmap -p- -sV -oX scan.xml target.com
python pendoc.py --nmap scan.xml --output results/
```

## Output (The Good Stuff)

### Directory Structure
```
output/
├── index.html                    # Open this in a browser, be amazed
├── screenshots/
│   ├── example.com/
│   │   └── desktop/
│   │       ├── index_20251120_153000.png
│   │       └── admin_20251120_153005.png
│   └── admin.example.com/
│       └── desktop/
│           └── login_20251120_153010.png
└── metadata/
    └── results.json              # Raw data for the nerds
```

### HTML Report Features
- Modern, responsive design (looks good on any device you shouldn't be pen testing from)
- Dark mode by default (because you have good taste)
- Searchable and filterable (find that one weird subdomain in seconds)
- Click-to-zoom screenshots (because squinting is for chumps)
- Grouped by domain (organized like you pretend your life is)
- Statistics dashboard (numbers to make you look smart)
- Metadata everywhere (page titles, HTTP status, tech stack, the works)

## Configuration (For The Control Freaks)

Edit `config/pendoc.yaml` to customize everything:

### Screenshots
```yaml
screenshots:
  viewports:
    desktop: { width: 1920, height: 1080 }  # Standard issue
    tablet: { width: 768, height: 1024 }    # If you're into that
    mobile: { width: 375, height: 667 }     # Masochist mode
  capture_desktop: true      # Obviously
  capture_tablet: false      # Probably not
  capture_mobile: false      # Definitely not unless you like waiting
  full_page: true            # Because half a page is useless
  timeout: 30                # Seconds before giving up on slow sites
  wait_after_load: 2000      # Let that janky JavaScript render
```

### Performance
```yaml
performance:
  concurrent_workers: 5      # More = faster, but your RAM will cry
  max_retries: 2            # How many times to try before saying "screw it"
  retry_delay: 5            # Seconds to wait before retry
```

### HTTP Settings
```yaml
http:
  follow_redirects: true    # Chase those 302s
  verify_ssl: false         # It's pen testing, we live dangerously
  user_agent: "Mozilla/5.0 ... PenDoc/1.0"  # Pretend we're a real browser
  headers: {}               # Add custom headers if you're fancy
```

### Input Processing
```yaml
input:
  default_protocol: "https"  # HTTPS all the things (it's 2025)
  http_ports: [80, 8000, 8080, 8888, 3000, 5000]
  https_ports: [443, 8443, 9443]
  exclude_patterns:          # Don't screenshot this garbage
    - ".*\\.js$"
    - ".*\\.css$"
    - ".*\\.jpg$"
    - ".*\\.png$"
```

### Enrichment
```yaml
enrichment:
  collect_headers: true      # HTTP headers (the good stuff)
  detect_technologies: true  # "Is that... PHP? In 2025?"
  collect_ssl_info: true     # Certificate details for the paranoid
  interesting_headers:       # Headers worth highlighting
    - "Server"
    - "X-Powered-By"
    - "Content-Security-Policy"
```

### Report Settings
```yaml
report:
  title: "PenDoc - Penetration Testing Documentation"
  group_by_domain: true      # Organization is sexy
  show_metadata: true        # All the juicy details
  theme: "dark"              # Light mode is for psychopaths
```

## What PenDoc Actually Does

### Metadata Enrichment
- **HTTP Information**: Status codes, headers, timing, page titles (the basics)
- **Security Headers**: Server, X-Powered-By, CSP, X-Frame-Options, HSTS (the security stuff)
- **Technology Detection**: Nginx? Apache? IIS? PHP? ASP.NET? We'll find it.
- **SSL/TLS Analysis**: Certificate info, expiration dates, all that PKI nonsense

### Error Handling (Because Things Break)
- Graceful timeout handling (won't rage quit on slow sites)
- Automatic retry mechanism (tries again because we believe in second chances)
- Detailed error messages (tells you what went wrong, not just "error")
- Keeps processing even when individual targets fail (the show must go on)

### Extensibility (For The Tinkerers)
- Modular parser architecture (add new input formats without crying)
- YAML-based configuration (edit with any text editor like a civilized human)
- Plugin-ready design (extend it, we dare you)
- JSON export (automate all the things)

## Use Cases (When You'd Use This)

### Reconnaissance Documentation
- Screenshot all discovered subdomains (because you found 300 of them with subfinder)
- Visual inventory of target infrastructure (pretty pictures for the report)
- Identify interesting pages (admin panels, anyone?)
- Create baseline for comparison (so you know when things change)

### Penetration Test Reports
- Document application interfaces (screenshot everything)
- Capture before/after exploitation (show your work)
- Show proof of access (receipts or it didn't happen)
- Visual evidence for findings (because screenshots > walls of text)

### Scope Verification
- Confirm target URLs are accessible (or not, that's important too)
- Verify correct applications (make sure you're testing the right stuff)
- Identify out-of-scope resources (don't accidentally hack the wrong thing)
- Document testing boundaries (CYA documentation)

### Workflow Integration
```bash
# Subdomain enumeration → PenDoc
subfinder -d example.com -o subdomains.txt
python pendoc.py --subdomains subdomains.txt --output recon/

# Port scanning → PenDoc
nmap -iL targets.txt -p- -sV -oX scan.xml
python pendoc.py --nmap scan.xml --output portscan/

# Burp Suite testing → PenDoc
# (Export sitemap from Burp, you know how)
python pendoc.py --burp sitemap.xml --output manual_test/
```

### Integration with Cronos Platform
```python
from database import db_util

# Export web hosts from Cronos
hosts = db_util.get_web_hosts(client_id='ABC123')

# Create input for PenDoc
with open('urls.txt', 'w') as f:
    for host in hosts:
        f.write(f"{host['url']}\n")

# Run PenDoc (automate all the documentation)
import subprocess
subprocess.run([
    'python', 'pendoc.py',
    '--urls', 'urls.txt',
    '--output', f'output/{client_id}_screenshots'
])
```

## Performance (How Fast Is This Thing?)

- **Speed**: ~5-10 targets/minute (depends on how slow the target sites are, not our fault)
- **Concurrency**: 5 parallel workers (configurable up to 20+ if your machine can handle it)
- **Memory**: ~500MB-2GB (scales with concurrency and how much RAM you're willing to sacrifice)
- **Network**: Efficient, reuses browser context (because we're not wasteful)

### Optimization Tips (Make It Faster)

1. **Concurrent Workers**: Start with 5, go higher if:
   - Your network can handle it
   - The targets aren't slow as molasses
   - Your laptop isn't from 2012

2. **Timeout Values**:
   - Fast networks: 15-20s (living life in the fast lane)
   - Slow targets: 30-60s (patience, grasshopper)
   - Very slow: 60-120s (make coffee, read a book)

3. **Viewport Selection**:
   - Desktop only: Fastest (recommended for sanity)
   - All viewports: 3x slower but looks impressive in reports

4. **Resource Filtering**:
   - Use `exclude_patterns` for static files
   - Skip the garbage, save time
   - Your SSD will thank you

5. **Batch Processing**:
   - Split massive target lists
   - Run multiple instances
   - Divide and conquer

## Common Issues (And How To Fix Them)

### Playwright not found
```bash
playwright install chromium
# That's it. That's the fix.
```

### SSL certificate errors
Set `verify_ssl: false` in `config/pendoc.yaml` (it's pen testing, we don't care about cert warnings)

### Timeouts on slow sites
Increase `timeout` value in `config/pendoc.yaml` (give the slow sites more time to wake up)

### Out of memory
Reduce `concurrent_workers` in `config/pendoc.yaml` (your laptop is crying for help)

### Import errors
```bash
pip install -r requirements.txt
# Did you skip the installation step? Come on.
```

## Testing (Make Sure It Works)

Run the test suite to validate your installation isn't borked:

```bash
python test_pendoc.py
```

This checks:
- All dependencies installed (did you run pip install?)
- All modules importable (no broken imports)
- Example files present (we included examples, don't delete them)
- Configuration valid (your YAML isn't garbage)
- Playwright browsers installed (did you run playwright install?)

## Examples (Sample Data Included)

The `examples/` directory has everything you need to test:
- `urls.txt` - Sample URL list
- `subdomains.txt` - Sample subdomain list
- `burp_sitemap_example.xml` - Sample Burp Suite export
- `nmap_example.xml` - Sample Nmap scan

Use these to make sure everything works before pointing it at real targets.

## Future Enhancements (Maybe Someday)

### Things We Might Add
- Authentication support (username/password, cookies, tokens)
- JavaScript interaction (click buttons, fill forms, be a real browser)
- Comparison mode (diff screenshots over time, spot changes)
- Advanced analysis (scan response bodies for fun stuff)
- PDF reports (because some people hate HTML)
- Masscan support (for when Nmap is too slow)

### Current Limitations (Things We Haven't Done Yet)
- No authentication support (can't log in automatically)
- No JavaScript interaction beyond page load (it's a screenshot tool, not a web driver)
- No custom cookies/sessions (yet)
- Can't screenshot multiple viewports in one run (run it multiple times, it's fast)

## Security Considerations (CYA Section)

- No credential storage (we don't want that liability)
- Local execution only (nothing phones home)
- Sanitized file paths (no directory traversal shenanigans)
- SSL verification configurable (disabled by default for pen testing)
- No remote code execution (it's screenshots, not shells)
- Safe for production use in pen testing context (but maybe not on prod)

## Requirements (What You Need)

- Python 3.10 or higher (if you're still on 2.7, we can't help you)
- Playwright with Chromium (downloads ~200MB, deal with it)
- 2GB RAM minimum (more if you increase concurrent workers)
- Network access to targets (duh)
- Common sense (optional but recommended)

## Contributing (Yes, Please)

Found a bug? Want a feature? Have a better ASCII art header?
- Report issues (tell us what broke)
- Suggest features (tell us what you want)
- Submit pull requests (tell us you fixed it yourself)
- Share integration examples (help others)

## Credits

Built with:
- **Modularity**: Easy to extend (add more parsers, we dare you)
- **Performance**: Concurrent processing (because time is money)
- **Usability**: Clear output (no PhD required)
- **Integration**: Works with existing tools (plays well with others)
- **Snark**: Excessive amounts (you're welcome)

## Quick Reference (Cheat Sheet)

```bash
# Installation (do this first)
pip install -r requirements.txt && playwright install chromium

# Basic usage (the simple version)
python pendoc.py --urls urls.txt -o output/

# Multiple sources (showing off)
python pendoc.py --urls u.txt --burp b.xml --subdomains s.txt --nmap n.xml -o out/

# Custom config (for control freaks)
python pendoc.py --urls urls.txt -c custom.yaml -o output/

# Test installation (make sure it works)
python test_pendoc.py

# Quick demo for Windows users
quicktest.bat
```

---

**Status**: Production-ready and battle-tested

**License**: Internal use only (don't redistribute, don't blame us if something breaks)

**Support**: Read the code, it's not that complicated

Now go forth and document your pen tests like a boss. Your future self (writing the report at 2 AM before the deadline) will thank you.

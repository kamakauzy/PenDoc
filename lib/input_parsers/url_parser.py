"""Parse simple URL list files"""

import logging
from pathlib import Path
from urllib.parse import urlparse
from lib.port_checker import QuickPortChecker


class URLParser:
    """Parser for simple URL list files"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Fast port checker: 1s timeout, 20 concurrent checks
        self.port_checker = QuickPortChecker(timeout=1.0, max_workers=20)
        self.auto_discover_ports = config.get('input', {}).get('auto_discover_ports', True)
    
    def parse(self, file_path: str) -> list:
        """
        Parse a file containing one URL per line
        
        Args:
            file_path: Path to file with URLs
            
        Returns:
            List of target dictionaries
        """
        targets = []
        
        # Try multiple encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.logger.debug(f"Successfully read file with {encoding} encoding")
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if content is None:
            self.logger.error(f"Could not decode file {file_path} with any supported encoding")
            return []
        
        try:
            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Check if this is a bare IP/hostname that needs port discovery
                if self.auto_discover_ports and self.port_checker.is_bare_ip_or_host(line):
                    self.logger.info(f"Bare IP/hostname detected: {line}, checking common web ports...")
                    discovered_services = self.port_checker.find_web_services(line)
                    
                    if discovered_services:
                        for service in discovered_services:
                            targets.append({
                                'url': service['url'],
                                'source': 'url_list_discovered',
                                'source_file': file_path,
                                'line_number': line_num,
                                'domain': service['host'],
                                'scheme': service['protocol'],
                                'port': service['port'],
                                'discovered_port': True
                            })
                        self.logger.info(f"Discovered {len(discovered_services)} web services on {line}")
                    else:
                        self.logger.warning(f"No web services found on {line}")
                    continue
                
                # Smart protocol handling for entries with ports
                if not line.startswith(('http://', 'https://')):
                    # Check if it has a port that suggests http vs https
                    if ':80' in line or ':8080' in line or ':8000' in line or ':3000' in line or ':5000' in line:
                        protocol = 'http'
                    elif ':443' in line or ':8443' in line:
                        protocol = 'https'
                    else:
                        protocol = self.config['input']['default_protocol']
                    
                    url = f"{protocol}://{line}"
                else:
                    url = line
                
                # Validate URL
                try:
                    parsed = urlparse(url)
                    
                    # Check if we have a netloc (domain/IP)
                    # urlparse can be weird with IPs, so let's be more lenient
                    if not parsed.netloc:
                        # Maybe urlparse failed, try a simpler check
                        # If we can split on :// and there's something after, it's probably valid
                        if '://' in url and len(url.split('://')[1]) > 0:
                            self.logger.debug(f"URL might be valid despite urlparse issues: {url}")
                            # Manual parsing
                            parts = url.split('://')
                            scheme = parts[0]
                            rest = parts[1]
                            netloc = rest.split('/')[0] if '/' in rest else rest
                            
                            targets.append({
                                'url': url,
                                'source': 'url_list',
                                'source_file': file_path,
                                'line_number': line_num,
                                'domain': netloc,
                                'scheme': scheme
                            })
                        else:
                            self.logger.warning(f"Invalid URL at line {line_num}: {line} -> {url}")
                            continue
                    else:
                        targets.append({
                            'url': url,
                            'source': 'url_list',
                            'source_file': file_path,
                            'line_number': line_num,
                            'domain': parsed.netloc,
                            'scheme': parsed.scheme,
                            'port': parsed.port if parsed.port else (443 if parsed.scheme == 'https' else 80)
                        })
                except Exception as e:
                    self.logger.warning(f"Error parsing URL at line {line_num} ({line}): {e}")
                    # Try to add it anyway if it looks URL-like
                    if '://' in url:
                        parts = url.split('://')
                        if len(parts) == 2 and parts[1]:
                            scheme = parts[0]
                            rest = parts[1]
                            netloc = rest.split('/')[0] if '/' in rest else rest
                            
                            targets.append({
                                'url': url,
                                'source': 'url_list',
                                'source_file': file_path,
                                'line_number': line_num,
                                'domain': netloc,
                                'scheme': scheme
                            })
                    continue
            
            self.logger.info(f"Parsed {len(targets)} URLs from {file_path}")
            return targets
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return []


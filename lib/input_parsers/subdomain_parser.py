"""Parse subdomain enumeration results"""

import logging
from pathlib import Path
import re


class SubdomainParser:
    """Parser for subdomain enumeration result files"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def parse(self, file_path: str) -> list:
        """
        Parse subdomain list file
        
        Supports various formats:
        - Simple list (one subdomain per line)
        - CSV format (domain,ip,...)
        - JSON format
        
        Args:
            file_path: Path to subdomain list
            
        Returns:
            List of target dictionaries
        """
        targets = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Try to detect format
            if content.strip().startswith('[') or content.strip().startswith('{'):
                targets = self._parse_json(content, file_path)
            elif ',' in content:
                targets = self._parse_csv(content, file_path)
            else:
                targets = self._parse_simple(content, file_path)
            
            self.logger.info(f"Parsed {len(targets)} subdomains from {file_path}")
            return targets
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return []
    
    def _parse_simple(self, content: str, source_file: str) -> list:
        """Parse simple list format (one subdomain per line)"""
        targets = []
        protocol = self.config['input']['default_protocol']
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Extract just the domain/subdomain (remove protocol if present)
            domain = re.sub(r'^https?://', '', line)
            domain = domain.split('/')[0]  # Remove path
            domain = domain.split(':')[0]  # Remove port
            
            if self._is_valid_domain(domain):
                url = f"{protocol}://{domain}"
                targets.append({
                    'url': url,
                    'source': 'subdomain_list',
                    'source_file': source_file,
                    'line_number': line_num,
                    'domain': domain,
                    'scheme': protocol
                })
        
        return targets
    
    def _parse_csv(self, content: str, source_file: str) -> list:
        """Parse CSV format (assumes domain in first column)"""
        targets = []
        protocol = self.config['input']['default_protocol']
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if not parts:
                continue
            
            domain = parts[0].strip()
            domain = re.sub(r'^https?://', '', domain)
            
            if self._is_valid_domain(domain):
                url = f"{protocol}://{domain}"
                targets.append({
                    'url': url,
                    'source': 'subdomain_csv',
                    'source_file': source_file,
                    'line_number': line_num,
                    'domain': domain,
                    'scheme': protocol
                })
        
        return targets
    
    def _parse_json(self, content: str, source_file: str) -> list:
        """Parse JSON format"""
        import json
        targets = []
        protocol = self.config['input']['default_protocol']
        
        try:
            data = json.loads(content)
            
            # Handle array of strings
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        domain = re.sub(r'^https?://', '', item)
                        if self._is_valid_domain(domain):
                            url = f"{protocol}://{domain}"
                            targets.append({
                                'url': url,
                                'source': 'subdomain_json',
                                'source_file': source_file,
                                'domain': domain,
                                'scheme': protocol
                            })
                    elif isinstance(item, dict) and 'domain' in item:
                        domain = item['domain']
                        if self._is_valid_domain(domain):
                            url = f"{protocol}://{domain}"
                            targets.append({
                                'url': url,
                                'source': 'subdomain_json',
                                'source_file': source_file,
                                'domain': domain,
                                'scheme': protocol
                            })
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format: {e}")
        
        return targets
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain format"""
        # Basic domain validation
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain)) and len(domain) <= 253


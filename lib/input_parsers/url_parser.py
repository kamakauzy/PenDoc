"""Parse simple URL list files"""

import logging
from pathlib import Path
from urllib.parse import urlparse


class URLParser:
    """Parser for simple URL list files"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
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
                
                # Add protocol if missing
                if not line.startswith(('http://', 'https://')):
                    protocol = self.config['input']['default_protocol']
                    url = f"{protocol}://{line}"
                else:
                    url = line
                
                # Validate URL
                try:
                    parsed = urlparse(url)
                    if not parsed.netloc:
                        self.logger.warning(f"Invalid URL at line {line_num}: {line}")
                        continue
                    
                    targets.append({
                        'url': url,
                        'source': 'url_list',
                        'source_file': file_path,
                        'line_number': line_num,
                        'domain': parsed.netloc,
                        'scheme': parsed.scheme
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing URL at line {line_num}: {e}")
                    continue
            
            self.logger.info(f"Parsed {len(targets)} URLs from {file_path}")
            return targets
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return []


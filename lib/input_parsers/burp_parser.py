"""Parse Burp Suite sitemap XML exports"""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import re


class BurpParser:
    """Parser for Burp Suite sitemap XML files"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def parse(self, file_path: str) -> list:
        """
        Parse Burp Suite sitemap XML file
        
        Args:
            file_path: Path to Burp sitemap XML
            
        Returns:
            List of target dictionaries
        """
        targets = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Burp sitemap format has <item> elements
            for item in root.findall('.//item'):
                try:
                    # Get URL
                    url_elem = item.find('url')
                    if url_elem is None or not url_elem.text:
                        continue
                    
                    url = url_elem.text
                    
                    # Skip excluded patterns
                    if self._should_exclude(url):
                        continue
                    
                    # Get response status
                    status_elem = item.find('.//status')
                    status_code = status_elem.text if status_elem is not None else None
                    
                    # Get response length
                    length_elem = item.find('.//responselength')
                    response_length = length_elem.text if length_elem is not None else None
                    
                    # Get mime type
                    mime_elem = item.find('.//mimetype')
                    mime_type = mime_elem.text if mime_elem is not None else None
                    
                    parsed = urlparse(url)
                    
                    targets.append({
                        'url': url,
                        'source': 'burp_sitemap',
                        'source_file': file_path,
                        'domain': parsed.netloc,
                        'scheme': parsed.scheme,
                        'path': parsed.path,
                        'burp_status': status_code,
                        'burp_length': response_length,
                        'burp_mime': mime_type
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Burp item: {e}")
                    continue
            
            self.logger.info(f"Parsed {len(targets)} items from Burp sitemap")
            return targets
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except ET.ParseError as e:
            self.logger.error(f"Invalid XML format in {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing Burp sitemap {file_path}: {e}")
            return []
    
    def _should_exclude(self, url: str) -> bool:
        """Check if URL matches exclusion patterns"""
        exclude_patterns = self.config['input'].get('exclude_patterns', [])
        
        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False


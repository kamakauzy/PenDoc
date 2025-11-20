"""Parse Nmap XML scan results"""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


class NmapParser:
    """Parser for Nmap XML scan results"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def parse(self, file_path: str) -> list:
        """
        Parse Nmap XML file and extract web services
        
        Args:
            file_path: Path to Nmap XML file
            
        Returns:
            List of target dictionaries
        """
        targets = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Process each host
            for host in root.findall('.//host'):
                # Get host address
                address_elem = host.find('.//address[@addrtype="ipv4"]')
                if address_elem is None:
                    address_elem = host.find('.//address[@addrtype="ipv6"]')
                
                if address_elem is None:
                    continue
                
                ip_address = address_elem.get('addr')
                
                # Get hostname if available
                hostname_elem = host.find('.//hostname')
                hostname = hostname_elem.get('name') if hostname_elem is not None else ip_address
                
                # Process ports
                for port in host.findall('.//port'):
                    port_num = port.get('portid')
                    protocol = port.get('protocol')
                    
                    if protocol != 'tcp':
                        continue
                    
                    # Check port state
                    state = port.find('state')
                    if state is None or state.get('state') != 'open':
                        continue
                    
                    # Get service info
                    service = port.find('service')
                    if service is None:
                        continue
                    
                    service_name = service.get('name', '')
                    service_product = service.get('product', '')
                    service_version = service.get('version', '')
                    tunnel = service.get('tunnel', '')
                    
                    # Determine if this is a web service
                    is_http, scheme = self._is_web_service(
                        int(port_num),
                        service_name,
                        tunnel
                    )
                    
                    if is_http:
                        url = f"{scheme}://{hostname}:{port_num}"
                        
                        targets.append({
                            'url': url,
                            'source': 'nmap_scan',
                            'source_file': file_path,
                            'domain': hostname,
                            'ip_address': ip_address,
                            'scheme': scheme,
                            'port': port_num,
                            'service_name': service_name,
                            'service_product': service_product,
                            'service_version': service_version
                        })
            
            self.logger.info(f"Parsed {len(targets)} web services from Nmap scan")
            return targets
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except ET.ParseError as e:
            self.logger.error(f"Invalid XML format in {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing Nmap scan {file_path}: {e}")
            return []
    
    def _is_web_service(self, port: int, service_name: str, tunnel: str) -> tuple:
        """
        Determine if service is HTTP/HTTPS
        
        Returns:
            (is_web_service, scheme)
        """
        # Check for SSL/TLS tunnel
        if tunnel == 'ssl':
            return True, 'https'
        
        # Check service name
        if service_name in ['http', 'http-proxy', 'http-alt']:
            # Check if it's a common HTTPS port
            if port in self.config['input']['https_ports']:
                return True, 'https'
            return True, 'http'
        
        if service_name in ['https', 'https-alt', 'ssl/http']:
            return True, 'https'
        
        # Check common HTTP ports
        if port in self.config['input']['http_ports']:
            return True, 'http'
        
        # Check common HTTPS ports
        if port in self.config['input']['https_ports']:
            return True, 'https'
        
        return False, 'http'


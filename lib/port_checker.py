"""Quick port checker for discovering web services"""

import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


class QuickPortChecker:
    """Fast port checking for common web ports"""
    
    # Common web ports to check
    COMMON_WEB_PORTS = {
        80: 'http',
        443: 'https',
        8000: 'http',
        8080: 'http',
        8443: 'https',
        8888: 'http',
        3000: 'http',
        5000: 'http',
        9000: 'http',
        9443: 'https',
    }
    
    def __init__(self, timeout: float = 3.0, max_workers: int = 10):
        """
        Initialize port checker
        
        Args:
            timeout: Connection timeout in seconds (default: 3.0 - balanced speed/accuracy)
            max_workers: Number of concurrent port checks (default: 10 - avoid overwhelming network)
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
    
    def check_port(self, host: str, port: int) -> bool:
        """
        Check if a port is open
        
        Args:
            host: IP address or hostname
            port: Port number to check
            
        Returns:
            True if port is open, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.debug(f"Error checking {host}:{port} - {e}")
            return False
    
    def find_web_services(self, host: str, ports: dict = None) -> list:
        """
        Find open web ports on a host
        
        Args:
            host: IP address or hostname
            ports: Dictionary of {port: protocol}, defaults to COMMON_WEB_PORTS
            
        Returns:
            List of URLs for open web services
        """
        if ports is None:
            ports = self.COMMON_WEB_PORTS
        
        open_services = []
        
        # Check ports concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_port = {
                executor.submit(self.check_port, host, port): (port, protocol)
                for port, protocol in ports.items()
            }
            
            for future in as_completed(future_to_port):
                port, protocol = future_to_port[future]
                try:
                    if future.result():
                        url = f"{protocol}://{host}:{port}"
                        open_services.append({
                            'url': url,
                            'host': host,
                            'port': port,
                            'protocol': protocol,
                            'discovered': True
                        })
                        self.logger.info(f"Found open port: {host}:{port} ({protocol})")
                except Exception as e:
                    self.logger.debug(f"Error processing result for {host}:{port} - {e}")
        
        return open_services
    
    def is_bare_ip_or_host(self, target: str) -> bool:
        """
        Check if target is a bare IP or hostname (no port, no protocol)
        
        Args:
            target: Target string
            
        Returns:
            True if it's a bare IP/hostname, False if it has port or protocol
        """
        # Has protocol
        if target.startswith(('http://', 'https://')):
            return False
        
        # Has port
        if ':' in target:
            # Could be IPv6, check if it's a port
            parts = target.split(':')
            if len(parts) == 2:
                try:
                    int(parts[1])  # If this works, it's a port
                    return False
                except ValueError:
                    pass
        
        return True


"""Metadata enrichment for targets"""

import logging
import ssl
import socket
from datetime import datetime
from typing import Dict, List
import requests
from urllib.parse import urlparse
import re
from lib.tech_fingerprinter import TechnologyFingerprinter


class EnrichmentEngine:
    """Enriches targets with additional metadata"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.fingerprinter = TechnologyFingerprinter()
        
        # Setup requests session
        self.session = requests.Session()
        self.session.verify = self.config['http']['verify_ssl']
        self.session.headers.update({
            'User-Agent': self.config['http']['user_agent']
        })
    
    def enrich_all(self, results: List[Dict]) -> List[Dict]:
        """
        Enrich all results with metadata
        
        Args:
            results: List of screenshot results
            
        Returns:
            Enriched results
        """
        for result in results:
            if result['status'] == 'success':
                try:
                    self._enrich_target(result)
                except Exception as e:
                    self.logger.warning(f"Error enriching {result.get('url')}: {e}")
        
        return results
    
    def _enrich_target(self, result: Dict):
        """Enrich single target with metadata"""
        url = result['url']
        
        # Fingerprint technologies
        detected_tech = self.fingerprinter.fingerprint_from_screenshot_result(result)
        if detected_tech:
            result['detected_technologies'] = detected_tech
            # Add to existing technologies list
            if 'technologies' not in result:
                result['technologies'] = []
            for tech in detected_tech:
                tech_name = tech['name'] if isinstance(tech, dict) else tech
                if tech_name not in result['technologies']:
                    result['technologies'].append(tech_name.title())
        
        # Collect SSL certificate info
        if self.config['enrichment']['collect_ssl_info'] and url.startswith('https'):
            result['ssl_info'] = self._get_ssl_info(url)
        
        # Detect technologies (existing method)
        if self.config['enrichment']['detect_technologies']:
            existing_tech = self._detect_technologies(result)
            if existing_tech:
                if 'technologies' not in result:
                    result['technologies'] = []
                result['technologies'].extend([t for t in existing_tech if t not in result['technologies']])
        
        # Extract interesting headers
        if self.config['enrichment']['collect_headers'] and 'http_headers' in result:
            result['interesting_headers'] = self._extract_interesting_headers(
                result['http_headers']
            )
    
    def _get_ssl_info(self, url: str) -> Dict:
        """Get SSL certificate information"""
        ssl_info = {}
        
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc.split(':')[0]
            port = parsed.port or 443
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        ssl_info['subject'] = dict(x[0] for x in cert.get('subject', []))
                        ssl_info['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                        ssl_info['version'] = cert.get('version')
                        ssl_info['not_before'] = cert.get('notBefore')
                        ssl_info['not_after'] = cert.get('notAfter')
                        ssl_info['serial_number'] = cert.get('serialNumber')
                        
                        # Check if expired
                        try:
                            not_after = datetime.strptime(
                                cert.get('notAfter'),
                                '%b %d %H:%M:%S %Y %Z'
                            )
                            ssl_info['is_expired'] = not_after < datetime.now()
                        except:
                            pass
        
        except Exception as e:
            self.logger.debug(f"Error getting SSL info for {url}: {e}")
        
        return ssl_info
    
    def _detect_technologies(self, result: Dict) -> List[str]:
        """
        Detect technologies used by the target
        Basic detection based on headers and patterns
        """
        technologies = []
        
        headers = result.get('http_headers', {})
        
        # Server detection
        server = headers.get('server', '').lower()
        if 'nginx' in server:
            technologies.append('Nginx')
        if 'apache' in server:
            technologies.append('Apache')
        if 'iis' in server:
            technologies.append('IIS')
        if 'cloudflare' in server:
            technologies.append('Cloudflare')
        
        # Framework detection from headers
        if 'x-powered-by' in headers:
            powered_by = headers['x-powered-by'].lower()
            if 'php' in powered_by:
                technologies.append('PHP')
            if 'asp.net' in powered_by:
                technologies.append('ASP.NET')
            if 'express' in powered_by:
                technologies.append('Express.js')
        
        if 'x-aspnet-version' in headers:
            technologies.append('ASP.NET')
        
        if 'x-framework' in headers:
            technologies.append(headers['x-framework'])
        
        # WAF detection
        waf_headers = [
            'x-sucuri-id', 'x-sucuri-cache',
            'cf-ray',
            'x-cdn', 'x-edge-location'
        ]
        for waf_header in waf_headers:
            if waf_header in headers:
                technologies.append('WAF/CDN')
                break
        
        return list(set(technologies))  # Remove duplicates
    
    def _extract_interesting_headers(self, headers: Dict) -> Dict:
        """Extract interesting security headers"""
        interesting = {}
        
        interesting_header_names = [
            h.lower() for h in self.config['enrichment']['interesting_headers']
        ]
        
        for header_name in interesting_header_names:
            if header_name in headers:
                interesting[header_name] = headers[header_name]
        
        return interesting


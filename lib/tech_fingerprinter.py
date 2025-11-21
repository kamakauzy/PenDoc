"""Technology fingerprinting for web applications"""

import logging
from typing import Dict, List
import re


class TechnologyFingerprinter:
    """Detect CMS, frameworks, and technologies from HTTP responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # CMS/Platform signatures
        self.signatures = {
            'wordpress': {
                'paths': ['/wp-content/', '/wp-includes/', '/wp-admin/', '/wp-login.php'],
                'headers': {'X-Powered-By': 'WordPress'},
                'body_patterns': ['wp-content', 'wp-includes', 'wordpress'],
                'priority': 'high'
            },
            'joomla': {
                'paths': ['/administrator/', '/components/', '/modules/', '/templates/'],
                'headers': {'X-Content-Encoded-By': 'Joomla'},
                'body_patterns': ['Joomla!', '/components/com_'],
                'priority': 'high'
            },
            'drupal': {
                'paths': ['/sites/default/', '/misc/drupal.js', '/core/'],
                'headers': {'X-Generator': 'Drupal'},
                'body_patterns': ['Drupal.settings', 'sites/default/files'],
                'priority': 'high'
            },
            'sharepoint': {
                'paths': ['/_layouts/', '/_vti_bin/', '/_api/'],
                'headers': {'MicrosoftSharePointTeamServices': '*', 'SPRequestGuid': '*'},
                'body_patterns': ['_spBodyOnLoadFunctionNames'],
                'priority': 'high'
            },
            'magento': {
                'paths': ['/skin/frontend/', '/js/mage/', '/media/catalog/'],
                'body_patterns': ['Mage.Cookies', 'var BLANK_URL'],
                'priority': 'medium'
            },
            'prestashop': {
                'paths': ['/modules/', '/themes/', '/img/'],
                'body_patterns': ['prestashop', 'PrestaShop'],
                'priority': 'medium'
            },
            'shopify': {
                'headers': {'X-ShopId': '*'},
                'body_patterns': ['cdn.shopify.com', 'Shopify.theme'],
                'priority': 'high'
            },
            'woocommerce': {
                'paths': ['/wp-content/plugins/woocommerce/'],
                'body_patterns': ['woocommerce', 'WooCommerce'],
                'priority': 'high'
            }
        }
    
    def fingerprint_from_response(self, url: str, status_code: int, 
                                  headers: Dict, body: str = None) -> List[str]:
        """
        Fingerprint technology from HTTP response
        
        Args:
            url: Target URL
            status_code: HTTP status code
            headers: HTTP response headers (lowercase keys)
            body: Response body (optional)
            
        Returns:
            List of detected technologies
        """
        detected = []
        
        # Check each signature
        for tech_name, sig in self.signatures.items():
            confidence = 0
            reasons = []
            
            # Check URL paths
            if 'paths' in sig:
                for path in sig['paths']:
                    if path.lower() in url.lower():
                        confidence += 30
                        reasons.append(f"path:{path}")
            
            # Check headers
            if 'headers' in sig and headers:
                for header, value in sig['headers'].items():
                    header_lower = header.lower()
                    if header_lower in headers:
                        if value == '*' or value.lower() in headers[header_lower].lower():
                            confidence += 40
                            reasons.append(f"header:{header}")
            
            # Check body patterns
            if 'body_patterns' in sig and body:
                body_lower = body.lower()
                for pattern in sig['body_patterns']:
                    if pattern.lower() in body_lower:
                        confidence += 20
                        reasons.append(f"body:{pattern}")
            
            # If confidence is high enough, add to detected
            if confidence >= 30:
                detected.append({
                    'name': tech_name,
                    'confidence': min(confidence, 100),
                    'reasons': reasons,
                    'priority': sig.get('priority', 'low')
                })
                self.logger.info(f"Detected {tech_name} on {url} (confidence: {confidence}%)")
        
        return detected
    
    def fingerprint_from_screenshot_result(self, result: Dict) -> List[str]:
        """
        Fingerprint from PenDoc screenshot result
        
        Args:
            result: Screenshot result dictionary
            
        Returns:
            List of detected technologies
        """
        url = result.get('url', '')
        status_code = result.get('http_status', 0)
        headers = result.get('http_headers', {})
        
        # Convert headers to lowercase keys
        headers_lower = {k.lower(): v for k, v in headers.items()} if headers else {}
        
        # We don't have response body from screenshots, but we can check URL and headers
        detected = self.fingerprint_from_response(url, status_code, headers_lower)
        
        return detected


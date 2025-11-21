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
            # WordPress Ecosystem
            'wordpress': {
                'paths': ['/wp-content/', '/wp-includes/', '/wp-admin/', '/wp-login.php'],
                'headers': {'X-Powered-By': 'WordPress'},
                'body_patterns': ['wp-content', 'wp-includes', 'wordpress'],
                'priority': 'high',
                'category': 'cms'
            },
            'woocommerce': {
                'paths': ['/wp-content/plugins/woocommerce/'],
                'body_patterns': ['woocommerce', 'WooCommerce'],
                'priority': 'high',
                'category': 'ecommerce'
            },
            
            # Joomla
            'joomla': {
                'paths': ['/administrator/', '/components/', '/modules/', '/templates/'],
                'headers': {'X-Content-Encoded-By': 'Joomla'},
                'body_patterns': ['Joomla!', '/components/com_', 'joomla'],
                'priority': 'high',
                'category': 'cms'
            },
            
            # Drupal
            'drupal': {
                'paths': ['/sites/default/', '/misc/drupal.js', '/core/', '/modules/'],
                'headers': {'X-Generator': 'Drupal'},
                'body_patterns': ['Drupal.settings', 'sites/default/files', 'drupal'],
                'priority': 'high',
                'category': 'cms'
            },
            
            # Microsoft
            'sharepoint': {
                'paths': ['/_layouts/', '/_vti_bin/', '/_api/', '/_catalogs/'],
                'headers': {'MicrosoftSharePointTeamServices': '*', 'SPRequestGuid': '*'},
                'body_patterns': ['_spBodyOnLoadFunctionNames', 'SharePoint'],
                'priority': 'high',
                'category': 'cms'
            },
            
            # E-commerce Platforms
            'magento': {
                'paths': ['/skin/frontend/', '/js/mage/', '/media/catalog/', '/magento_version'],
                'body_patterns': ['Mage.Cookies', 'var BLANK_URL', 'Magento'],
                'priority': 'high',
                'category': 'ecommerce'
            },
            'prestashop': {
                'paths': ['/modules/', '/themes/', '/img/'],
                'body_patterns': ['prestashop', 'PrestaShop'],
                'priority': 'high',
                'category': 'ecommerce'
            },
            'shopify': {
                'headers': {'X-ShopId': '*'},
                'body_patterns': ['cdn.shopify.com', 'Shopify.theme', 'myshopify.com'],
                'priority': 'high',
                'category': 'ecommerce'
            },
            'opencart': {
                'paths': ['/catalog/', '/image/'],
                'body_patterns': ['catalog/view/theme/', 'OpenCart'],
                'priority': 'medium',
                'category': 'ecommerce'
            },
            'wix': {
                'body_patterns': ['wix.com', 'wixsite.com', 'X-Wix-'],
                'headers': {'X-Wix-Request-Id': '*', 'X-Wix-Renderer-Server': '*'},
                'priority': 'high',
                'category': 'website_builder'
            },
            'squarespace': {
                'body_patterns': ['squarespace.com', 'squarespace-cdn'],
                'headers': {'X-Served-By': 'squarespace'},
                'priority': 'high',
                'category': 'website_builder'
            },
            
            # Other CMSs
            'typo3': {
                'paths': ['/typo3/', '/typo3conf/', '/fileadmin/'],
                'headers': {'X-TYPO3-Parsetime': '*'},
                'body_patterns': ['typo3', 'TYPO3'],
                'priority': 'high',
                'category': 'cms'
            },
            'concrete5': {
                'paths': ['/concrete/', '/packages/', '/application/'],
                'body_patterns': ['concrete5', 'Concrete CMS'],
                'priority': 'medium',
                'category': 'cms'
            },
            'umbraco': {
                'paths': ['/umbraco/', '/umbraco_client/'],
                'body_patterns': ['Umbraco', 'umbraco'],
                'priority': 'medium',
                'category': 'cms'
            },
            'dotnetnuke': {
                'paths': ['/Portals/', '/DesktopModules/', '/DNN_Platform/'],
                'headers': {'X-Powered-By': 'DNN'},
                'body_patterns': ['DotNetNuke', 'DNN Platform'],
                'priority': 'medium',
                'category': 'cms'
            },
            'sitefinity': {
                'paths': ['/Sitefinity/', '/SFRes/'],
                'body_patterns': ['Sitefinity', 'sitefinity'],
                'priority': 'medium',
                'category': 'cms'
            },
            'kentico': {
                'paths': ['/CMSPages/', '/CMSModules/'],
                'body_patterns': ['Kentico', 'CMSPages'],
                'priority': 'medium',
                'category': 'cms'
            },
            'craft': {
                'paths': ['/cpresources/', '/actions/'],
                'headers': {'X-Powered-By': 'Craft CMS'},
                'body_patterns': ['Craft CMS', 'craftcms'],
                'priority': 'medium',
                'category': 'cms'
            },
            'ghost': {
                'paths': ['/ghost/', '/content/'],
                'headers': {'X-Powered-By': 'Ghost'},
                'body_patterns': ['ghost.org', 'content/images/'],
                'priority': 'medium',
                'category': 'cms'
            },
            
            # Forums
            'vbulletin': {
                'paths': ['/vbulletin/', '/clientscript/'],
                'body_patterns': ['vBulletin', 'vbulletin'],
                'priority': 'medium',
                'category': 'forum'
            },
            'phpbb': {
                'paths': ['/phpbb/', '/styles/'],
                'body_patterns': ['phpBB', 'Powered by phpBB'],
                'priority': 'medium',
                'category': 'forum'
            },
            'mybb': {
                'paths': ['/inc/', '/cache/'],
                'body_patterns': ['MyBB', 'mybb'],
                'priority': 'medium',
                'category': 'forum'
            },
            'discourse': {
                'headers': {'X-Discourse-Route': '*'},
                'body_patterns': ['discourse', 'Discourse'],
                'priority': 'medium',
                'category': 'forum'
            },
            
            # Wikis & Documentation
            'confluence': {
                'paths': ['/confluence/', '/wiki/'],
                'headers': {'X-Confluence-Request-Time': '*'},
                'body_patterns': ['Confluence', 'confluence'],
                'priority': 'high',
                'category': 'wiki'
            },
            'mediawiki': {
                'paths': ['/mediawiki/', '/wiki/'],
                'headers': {'X-Powered-By': 'MediaWiki'},
                'body_patterns': ['MediaWiki', 'mw-data'],
                'priority': 'medium',
                'category': 'wiki'
            },
            
            # Frameworks (for context)
            'asp.net': {
                'headers': {'X-AspNet-Version': '*', 'X-Powered-By': 'ASP.NET'},
                'body_patterns': ['__VIEWSTATE', '__EVENTVALIDATION'],
                'priority': 'low',
                'category': 'framework'
            },
            'laravel': {
                'headers': {'X-Powered-By': 'Laravel'},
                'body_patterns': ['laravel', 'csrf-token'],
                'priority': 'low',
                'category': 'framework'
            },
            'django': {
                'headers': {'X-Frame-Options': 'DENY'},
                'body_patterns': ['csrfmiddlewaretoken', 'django'],
                'priority': 'low',
                'category': 'framework'
            },
            'express': {
                'headers': {'X-Powered-By': 'Express'},
                'priority': 'low',
                'category': 'framework'
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


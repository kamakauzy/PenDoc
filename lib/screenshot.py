"""Screenshot capture engine using Playwright"""

import logging
from pathlib import Path
from datetime import datetime
import asyncio
import json
from typing import List, Dict
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from tqdm import tqdm


class ScreenshotEngine:
    """Handles screenshot capture using Playwright"""
    
    def __init__(self, config: dict, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.screenshot_dir = output_dir / 'screenshots'
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = output_dir / '.pendoc_progress.json'
        self.logger = logging.getLogger(__name__)
    
    def save_progress(self, results: List[Dict]):
        """Save current progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.debug(f"Saved progress: {len(results)} results")
        except Exception as e:
            self.logger.warning(f"Could not save progress: {e}")
    
    def load_progress(self) -> List[Dict]:
        """Load existing progress from file"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    results = json.load(f)
                self.logger.info(f"Loaded {len(results)} existing results from previous run")
                return results
            except Exception as e:
                self.logger.warning(f"Could not load progress file: {e}")
        return []
        
    def capture_all(self, targets: List[Dict], resume: bool = False) -> List[Dict]:
        """
        Capture screenshots for all targets
        
        Args:
            targets: List of target dictionaries
            resume: If True, load and continue from previous progress
            
        Returns:
            List of results with screenshot paths and metadata
        """
        # Load existing progress if resuming
        existing_results = []
        if resume:
            existing_results = self.load_progress()
            if existing_results:
                # Get URLs that are already done
                completed_urls = {r['url'] for r in existing_results}
                # Filter out completed targets
                remaining_targets = [t for t in targets if t['url'] not in completed_urls]
                
                if not remaining_targets:
                    self.logger.info("All targets already processed!")
                    return existing_results
                
                self.logger.info(f"Resuming: {len(existing_results)} already done, {len(remaining_targets)} remaining")
                targets = remaining_targets
        
        # Run async capture
        results = asyncio.run(self._capture_all_async(targets, existing_results))
        return results
    
    async def _capture_all_async(self, targets: List[Dict], existing_results: List[Dict] = None) -> List[Dict]:
        """Async screenshot capture with concurrency"""
        if existing_results is None:
            existing_results = []
        
        async with async_playwright() as p:
            # Launch browser with stealth options
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            # Realistic user agent (latest Chrome on Windows)
            user_agent = (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create browser context with WAF bypass settings
            context = await browser.new_context(
                user_agent=user_agent,
                ignore_https_errors=not self.config['http']['verify_ssl'],
                viewport={
                    'width': self.config['screenshots']['viewports']['desktop']['width'],
                    'height': self.config['screenshots']['viewports']['desktop']['height']
                },
                # Additional headers to look like real browser
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                }
            )
            
            # Remove webdriver flag (common WAF detection)
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add realistic plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Add realistic languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Chrome runtime
                window.chrome = {
                    runtime: {}
                };
            """)
            
            # Process targets with concurrency limit
            max_workers = self.config['performance']['concurrent_workers']
            results = list(existing_results)  # Start with existing results
            
            # Use tqdm for progress bar
            if self.config['logging']['show_progress']:
                pbar = tqdm(total=len(targets), desc="Capturing screenshots", unit="target")
            
            # Process in batches
            for i in range(0, len(targets), max_workers):
                batch = targets[i:i + max_workers]
                batch_results = await asyncio.gather(
                    *[self._capture_target(context, target) for target in batch],
                    return_exceptions=True
                )
                
                # Handle results
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Batch error: {result}")
                        results.append({
                            'status': 'failed',
                            'error': str(result)
                        })
                    else:
                        results.append(result)
                
                # Save progress after each batch
                self.save_progress(results)
                
                if self.config['logging']['show_progress']:
                    pbar.update(len(batch))
            
            if self.config['logging']['show_progress']:
                pbar.close()
            
            # Safe cleanup - catch exceptions if browser/context already closed
            try:
                await context.close()
            except Exception as e:
                self.logger.debug(f"Context already closed or error during close: {e}")
            
            try:
                await browser.close()
            except Exception as e:
                self.logger.debug(f"Browser already closed or error during close: {e}")
            
            return results
    
    async def _capture_target(self, context, target: Dict) -> Dict:
        """
        Capture screenshot for a single target
        
        Args:
            context: Playwright browser context
            target: Target dictionary
            
        Returns:
            Result dictionary with screenshot info
        """
        url = target['url']
        result = {
            **target,
            'status': 'pending',
            'screenshots': {},
            'timestamp': datetime.now().isoformat()
        }
        
        retries = 0
        max_retries = self.config['performance']['max_retries']
        
        while retries <= max_retries:
            try:
                # Create new page
                page = await context.new_page()
                
                # Navigate to URL
                timeout = self.config['screenshots']['timeout'] * 1000
                response = await page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=timeout
                )
                
                # Wait additional time for JS rendering
                await asyncio.sleep(self.config['screenshots']['wait_after_load'] / 1000)
                
                # Get response metadata
                if response:
                    result['http_status'] = response.status
                    result['http_headers'] = await response.all_headers()
                
                # Get page title
                result['page_title'] = await page.title()
                
                # Capture screenshots for enabled viewports
                viewports = self.config['screenshots']['viewports']
                
                if self.config['screenshots']['capture_desktop']:
                    await self._capture_viewport(
                        page, result, 'desktop',
                        viewports['desktop']
                    )
                
                if self.config['screenshots'].get('capture_tablet'):
                    await page.set_viewport_size(viewports['tablet'])
                    await self._capture_viewport(
                        page, result, 'tablet',
                        viewports['tablet']
                    )
                
                if self.config['screenshots'].get('capture_mobile'):
                    await page.set_viewport_size(viewports['mobile'])
                    await self._capture_viewport(
                        page, result, 'mobile',
                        viewports['mobile']
                    )
                
                result['status'] = 'success'
                await page.close()
                break
                
            except PlaywrightTimeout:
                retries += 1
                if retries > max_retries:
                    result['status'] = 'failed'
                    result['error'] = 'Timeout'
                    self.logger.warning(f"Timeout capturing {url}")
                else:
                    await asyncio.sleep(self.config['performance']['retry_delay'])
                    
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    result['status'] = 'failed'
                    result['error'] = str(e)
                    self.logger.warning(f"Error capturing {url}: {e}")
                else:
                    await asyncio.sleep(self.config['performance']['retry_delay'])
            
            finally:
                try:
                    if 'page' in locals():
                        await page.close()
                except:
                    pass
        
        return result
    
    async def _capture_viewport(self, page, result: Dict, viewport_name: str, viewport_size: Dict):
        """Capture screenshot for specific viewport"""
        url = result['url']
        parsed = urlparse(url)
        
        # Create organized directory structure
        domain = parsed.netloc.replace(':', '_')
        screenshot_subdir = self.screenshot_dir / domain / viewport_name
        screenshot_subdir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        path = parsed.path.strip('/').replace('/', '_') or 'index'
        if len(path) > 100:
            path = path[:100]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{path}_{timestamp}.png"
        screenshot_path = screenshot_subdir / filename
        
        # Capture screenshot
        await page.screenshot(
            path=str(screenshot_path),
            full_page=self.config['screenshots']['full_page']
        )
        
        result['screenshots'][viewport_name] = str(screenshot_path)


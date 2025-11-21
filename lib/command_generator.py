"""Generate command files for downstream pen testing tools"""

import logging
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


class CommandGenerator:
    """Generate command files for pen testing tools based on discovered technologies"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Create commands directory
        self.commands_dir = output_dir / 'commands'
        self.commands_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all(self, results: List[Dict]) -> Dict[str, str]:
        """
        Generate all command files
        
        Args:
            results: List of screenshot results with technology detections
            
        Returns:
            Dictionary of generated files and their paths
        """
        generated_files = {}
        
        # Group targets by technology
        wordpress_sites = []
        all_https_sites = []
        all_http_sites = []
        
        for result in results:
            if result.get('status') != 'success':
                continue
            
            url = result.get('url', '')
            technologies = result.get('detected_technologies', [])
            
            # Check for WordPress
            tech_names = [t['name'] if isinstance(t, dict) else t for t in technologies]
            if 'wordpress' in tech_names or 'woocommerce' in tech_names:
                wordpress_sites.append(result)
            
            # Collect all sites for general scanning
            if url.startswith('https://'):
                all_https_sites.append(result)
            elif url.startswith('http://'):
                all_http_sites.append(result)
        
        # Generate testssl commands
        if all_https_sites:
            testssl_file = self.generate_testssl_commands(all_https_sites)
            generated_files['testssl'] = str(testssl_file)
        
        # Generate nikto commands
        if all_https_sites or all_http_sites:
            nikto_file = self.generate_nikto_commands(all_https_sites + all_http_sites)
            generated_files['nikto'] = str(nikto_file)
        
        # Generate wpscan commands
        if wordpress_sites:
            wpscan_file = self.generate_wpscan_commands(wordpress_sites)
            generated_files['wpscan'] = str(wpscan_file)
        
        # Generate target lists
        targets_file = self.generate_target_lists(results)
        generated_files['targets'] = str(targets_file)
        
        return generated_files
    
    def generate_testssl_commands(self, https_sites: List[Dict]) -> Path:
        """
        Generate testssl.sh command file
        
        Format: testssl --file cmds.txt
        where cmds.txt contains:
        --vulnerable --cipher-per-proto --html domain.com
        """
        cmds_file = self.commands_dir / 'testssl_cmds.txt'
        
        with open(cmds_file, 'w') as f:
            for result in https_sites:
                url = result.get('url', '')
                # Extract domain from URL
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                
                # Write command for testssl
                f.write(f"--vulnerable --cipher-per-proto --html {domain}\n")
        
        self.logger.info(f"Generated testssl commands for {len(https_sites)} HTTPS sites")
        
        # Also create a run script
        run_script = self.commands_dir / 'run_testssl.sh'
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated testssl.sh commands by PenDoc\n\n")
            f.write(f"testssl --file {cmds_file.name}\n")
        run_script.chmod(0o755)
        
        return cmds_file
    
    def generate_nikto_commands(self, sites: List[Dict]) -> Path:
        """
        Generate nikto command file
        
        Format: nikto -h targets.txt -o output.htm
        """
        # Create targets file
        targets_file = self.commands_dir / 'nikto_targets.txt'
        
        with open(targets_file, 'w') as f:
            for result in sites:
                url = result.get('url', '')
                f.write(f"{url}\n")
        
        self.logger.info(f"Generated nikto targets for {len(sites)} sites")
        
        # Create run script
        run_script = self.commands_dir / 'run_nikto.sh'
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated nikto commands by PenDoc\n\n")
            f.write(f"nikto -h {targets_file.name} -o nikto_results.htm\n")
        run_script.chmod(0o755)
        
        return targets_file
    
    def generate_wpscan_commands(self, wordpress_sites: List[Dict]) -> Path:
        """
        Generate wpscan commands for WordPress sites
        
        Format: wpscan --stealthy --url site.com --api-token TOKEN
        """
        run_script = self.commands_dir / 'run_wpscan.sh'
        
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated wpscan commands by PenDoc\n")
            f.write("# Set your WPScan API token:\n")
            f.write('# export WPSCAN_TOKEN="your-token-here"\n\n')
            
            for result in wordpress_sites:
                url = result.get('url', '')
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                safe_filename = domain.replace(':', '_').replace('/', '_')
                
                f.write(f"echo 'Scanning {domain}...'\n")
                f.write(f"wpscan --stealthy --url {url} ")
                f.write(f"--api-token $WPSCAN_TOKEN > wpscan_{safe_filename}.txt\n\n")
        
        run_script.chmod(0o755)
        
        self.logger.info(f"Generated wpscan commands for {len(wordpress_sites)} WordPress sites")
        
        return run_script
    
    def generate_target_lists(self, results: List[Dict]) -> Path:
        """
        Generate various target list files for different tools
        """
        # All URLs
        all_urls_file = self.commands_dir / 'all_targets.txt'
        with open(all_urls_file, 'w') as f:
            for result in results:
                if result.get('status') == 'success':
                    f.write(f"{result.get('url', '')}\n")
        
        # Domains only (for tools that need just domains)
        domains_file = self.commands_dir / 'domains.txt'
        domains = set()
        for result in results:
            if result.get('status') == 'success':
                url = result.get('url', '')
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                domains.add(domain)
        
        with open(domains_file, 'w') as f:
            for domain in sorted(domains):
                f.write(f"{domain}\n")
        
        # IPs only
        ips_file = self.commands_dir / 'ips.txt'
        ips = set()
        for result in results:
            if result.get('status') == 'success':
                domain = result.get('domain', '')
                # Check if it's an IP
                if all(c in '0123456789.:' for c in domain):
                    ips.add(domain.split(':')[0])  # Remove port
        
        if ips:
            with open(ips_file, 'w') as f:
                for ip in sorted(ips):
                    f.write(f"{ip}\n")
        
        # Create master run script
        master_script = self.commands_dir / 'run_all_scans.sh'
        with open(master_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Master script to run all generated pen test commands\n")
            f.write("# Generated by PenDoc\n\n")
            
            f.write("echo 'Starting automated pen testing workflow...'\n")
            f.write("echo ''\n\n")
            
            if (self.commands_dir / 'run_testssl.sh').exists():
                f.write("echo '[1/3] Running testssl.sh scans...'\n")
                f.write("./run_testssl.sh\n")
                f.write("echo ''\n\n")
            
            if (self.commands_dir / 'run_nikto.sh').exists():
                f.write("echo '[2/3] Running nikto scans...'\n")
                f.write("./run_nikto.sh\n")
                f.write("echo ''\n\n")
            
            if (self.commands_dir / 'run_wpscan.sh').exists():
                f.write("echo '[3/3] Running wpscan...'\n")
                f.write("./run_wpscan.sh\n")
                f.write("echo ''\n\n")
            
            f.write("echo 'All scans complete!'\n")
        
        master_script.chmod(0o755)
        
        self.logger.info(f"Generated target lists: {all_urls_file.name}, {domains_file.name}")
        
        return all_urls_file


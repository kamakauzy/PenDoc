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
        cms_targets = defaultdict(list)
        all_https_sites = []
        all_http_sites = []
        
        for result in results:
            if result.get('status') != 'success':
                continue
            
            url = result.get('url', '')
            technologies = result.get('detected_technologies', [])
            
            # Extract technology names
            tech_names = []
            for t in technologies:
                if isinstance(t, dict):
                    tech_names.append(t['name'])
                else:
                    tech_names.append(str(t).lower())
            
            # Categorize by CMS
            for tech in tech_names:
                tech_lower = tech.lower()
                if tech_lower in ['wordpress', 'woocommerce']:
                    cms_targets['wordpress'].append(result)
                elif tech_lower == 'joomla':
                    cms_targets['joomla'].append(result)
                elif tech_lower == 'drupal':
                    cms_targets['drupal'].append(result)
                elif tech_lower == 'sharepoint':
                    cms_targets['sharepoint'].append(result)
                elif tech_lower in ['magento', 'prestashop', 'opencart']:
                    cms_targets['ecommerce'].append(result)
                elif tech_lower in ['typo3', 'concrete5', 'umbraco', 'dotnetnuke', 'ghost']:
                    cms_targets['other_cms'].append(result)
                elif tech_lower in ['vbulletin', 'phpbb', 'mybb', 'discourse']:
                    cms_targets['forum'].append(result)
                elif tech_lower in ['confluence', 'mediawiki']:
                    cms_targets['wiki'].append(result)
            
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
        
        # Generate CMS-specific commands
        if cms_targets['wordpress']:
            wpscan_file = self.generate_wpscan_commands(cms_targets['wordpress'])
            generated_files['wpscan'] = str(wpscan_file)
        
        if cms_targets['joomla']:
            joomscan_file = self.generate_joomscan_commands(cms_targets['joomla'])
            generated_files['joomscan'] = str(joomscan_file)
        
        if cms_targets['drupal']:
            droopescan_file = self.generate_droopescan_commands(cms_targets['drupal'])
            generated_files['droopescan'] = str(droopescan_file)
        
        if cms_targets['sharepoint']:
            sharepoint_file = self.generate_sharepoint_commands(cms_targets['sharepoint'])
            generated_files['sharepoint'] = str(sharepoint_file)
        
        # Generate nuclei commands for all sites
        if all_https_sites or all_http_sites:
            nuclei_file = self.generate_nuclei_commands(all_https_sites + all_http_sites, cms_targets)
            generated_files['nuclei'] = str(nuclei_file)
        
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
    
    def generate_joomscan_commands(self, joomla_sites: List[Dict]) -> Path:
        """
        Generate joomscan commands for Joomla sites
        
        Format: joomscan -u site.com
        """
        run_script = self.commands_dir / 'run_joomscan.sh'
        
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated joomscan commands by PenDoc\n")
            f.write("# Install: pip install joomscan OR git clone https://github.com/OWASP/joomscan.git\n\n")
            
            for result in joomla_sites:
                url = result.get('url', '')
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                safe_filename = domain.replace(':', '_').replace('/', '_')
                
                f.write(f"echo 'Scanning {domain}...'\n")
                f.write(f"joomscan -u {url} > joomscan_{safe_filename}.txt\n\n")
        
        run_script.chmod(0o755)
        
        self.logger.info(f"Generated joomscan commands for {len(joomla_sites)} Joomla sites")
        
        return run_script
    
    def generate_droopescan_commands(self, drupal_sites: List[Dict]) -> Path:
        """
        Generate droopescan commands for Drupal sites
        
        Format: droopescan scan drupal -u site.com
        """
        run_script = self.commands_dir / 'run_droopescan.sh'
        
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated droopescan commands by PenDoc\n")
            f.write("# Install: pip install droopescan\n\n")
            
            for result in drupal_sites:
                url = result.get('url', '')
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                safe_filename = domain.replace(':', '_').replace('/', '_')
                
                f.write(f"echo 'Scanning {domain}...'\n")
                f.write(f"droopescan scan drupal -u {url} > droopescan_{safe_filename}.txt\n\n")
        
        run_script.chmod(0o755)
        
        self.logger.info(f"Generated droopescan commands for {len(drupal_sites)} Drupal sites")
        
        return run_script
    
    def generate_sharepoint_commands(self, sharepoint_sites: List[Dict]) -> Path:
        """
        Generate SharePoint enumeration commands
        
        Uses various SharePoint enumeration techniques
        """
        run_script = self.commands_dir / 'run_sharepoint_enum.sh'
        
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated SharePoint enumeration commands by PenDoc\n")
            f.write("# Install: pip install sparty OR git clone https://github.com/0xdevalias/sharepwn\n\n")
            
            # Create targets file
            targets_file = self.commands_dir / 'sharepoint_targets.txt'
            with open(targets_file, 'w') as tf:
                for result in sharepoint_sites:
                    url = result.get('url', '')
                    tf.write(f"{url}\n")
            
            f.write("# Common SharePoint enumeration endpoints\n")
            f.write("echo 'Enumerating SharePoint sites...'\n\n")
            
            for result in sharepoint_sites:
                url = result.get('url', '')
                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                safe_filename = domain.replace(':', '_').replace('/', '_')
                
                f.write(f"echo 'Checking {domain}...'\n")
                f.write(f"# Common SharePoint paths\n")
                f.write(f"curl -k -s {url}/_api/web/lists >> sharepoint_{safe_filename}_enum.txt\n")
                f.write(f"curl -k -s {url}/_vti_bin/listdata.svc >> sharepoint_{safe_filename}_enum.txt\n")
                f.write(f"curl -k -s {url}/_layouts/viewlsts.aspx >> sharepoint_{safe_filename}_enum.txt\n\n")
        
        run_script.chmod(0o755)
        
        self.logger.info(f"Generated SharePoint enumeration commands for {len(sharepoint_sites)} sites")
        
        return run_script
    
    def generate_nuclei_commands(self, all_sites: List[Dict], cms_targets: Dict) -> Path:
        """
        Generate nuclei commands with CMS-specific templates
        
        Format: nuclei -l targets.txt -t cms/
        """
        run_script = self.commands_dir / 'run_nuclei.sh'
        
        with open(run_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated nuclei commands by PenDoc\n")
            f.write("# Install: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest\n\n")
            
            # All sites
            f.write("echo 'Running nuclei scans...'\n\n")
            
            # WordPress specific
            if cms_targets.get('wordpress'):
                wp_targets = self.commands_dir / 'wordpress_targets.txt'
                with open(wp_targets, 'w') as wt:
                    for result in cms_targets['wordpress']:
                        wt.write(f"{result.get('url', '')}\n")
                
                f.write("echo '[1] WordPress vulnerabilities...'\n")
                f.write(f"nuclei -l {wp_targets.name} -t wordpress/ -o nuclei_wordpress_results.txt\n\n")
            
            # Joomla specific
            if cms_targets.get('joomla'):
                joomla_targets = self.commands_dir / 'joomla_targets.txt'
                with open(joomla_targets, 'w') as jt:
                    for result in cms_targets['joomla']:
                        jt.write(f"{result.get('url', '')}\n")
                
                f.write("echo '[2] Joomla vulnerabilities...'\n")
                f.write(f"nuclei -l {joomla_targets.name} -t joomla/ -o nuclei_joomla_results.txt\n\n")
            
            # Drupal specific
            if cms_targets.get('drupal'):
                drupal_targets = self.commands_dir / 'drupal_targets.txt'
                with open(drupal_targets, 'w') as dt:
                    for result in cms_targets['drupal']:
                        dt.write(f"{result.get('url', '')}\n")
                
                f.write("echo '[3] Drupal vulnerabilities...'\n")
                f.write(f"nuclei -l {drupal_targets.name} -t drupal/ -o nuclei_drupal_results.txt\n\n")
            
            # Generic CMS scans
            f.write("echo '[4] Generic CMS vulnerabilities...'\n")
            f.write(f"nuclei -l all_targets.txt -t cms/ -o nuclei_cms_results.txt\n\n")
            
            f.write("echo 'Nuclei scans complete!'\n")
        
        run_script.chmod(0o755)
        
        self.logger.info(f"Generated nuclei commands for {len(all_sites)} sites")
        
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
            
            f.write("echo '===================================='\n")
            f.write("echo '  PenDoc - Automated Pen Test Suite'\n")
            f.write("echo '===================================='\n")
            f.write("echo ''\n\n")
            
            step = 1
            
            # testssl
            if (self.commands_dir / 'run_testssl.sh').exists():
                f.write(f"echo '[{step}] Running testssl.sh scans...'\n")
                f.write("./run_testssl.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            # nikto
            if (self.commands_dir / 'run_nikto.sh').exists():
                f.write(f"echo '[{step}] Running nikto scans...'\n")
                f.write("./run_nikto.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            # nuclei
            if (self.commands_dir / 'run_nuclei.sh').exists():
                f.write(f"echo '[{step}] Running nuclei scans...'\n")
                f.write("./run_nuclei.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            # wpscan
            if (self.commands_dir / 'run_wpscan.sh').exists():
                f.write(f"echo '[{step}] Running wpscan (WordPress)...'\n")
                f.write("./run_wpscan.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            # joomscan
            if (self.commands_dir / 'run_joomscan.sh').exists():
                f.write(f"echo '[{step}] Running joomscan (Joomla)...'\n")
                f.write("./run_joomscan.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            # droopescan
            if (self.commands_dir / 'run_droopescan.sh').exists():
                f.write(f"echo '[{step}] Running droopescan (Drupal)...'\n")
                f.write("./run_droopescan.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            # sharepoint
            if (self.commands_dir / 'run_sharepoint_enum.sh').exists():
                f.write(f"echo '[{step}] Running SharePoint enumeration...'\n")
                f.write("./run_sharepoint_enum.sh\n")
                f.write("echo ''\n\n")
                step += 1
            
            f.write("echo '===================================='\n")
            f.write("echo '  All scans complete!'\n")
            f.write("echo '===================================='\n")
        
        master_script.chmod(0o755)
        
        self.logger.info(f"Generated target lists: {all_urls_file.name}, {domains_file.name}")
        
        return all_urls_file


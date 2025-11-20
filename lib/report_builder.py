"""HTML report generation"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse
from jinja2 import Template


class ReportBuilder:
    """Generates HTML reports from results"""
    
    def __init__(self, config: dict, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
    
    def generate(self, results: List[Dict]) -> str:
        """
        Generate HTML report
        
        Args:
            results: List of enriched results
            
        Returns:
            Path to generated report
        """
        # Save metadata
        metadata_dir = self.output_dir / 'metadata'
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / 'results.json'
        with open(metadata_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Group results if configured
        if self.config['report']['group_by_domain']:
            grouped = self._group_by_domain(results)
        else:
            grouped = {'All Targets': results}
        
        # Generate statistics
        stats = self._generate_stats(results)
        
        # Render HTML
        html = self._render_html(grouped, stats)
        
        # Write report
        report_path = self.output_dir / 'index.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Report generated: {report_path}")
        return str(report_path)
    
    def _group_by_domain(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group results by domain"""
        grouped = {}
        
        for result in results:
            domain = result.get('domain', 'Unknown')
            if domain not in grouped:
                grouped[domain] = []
            grouped[domain].append(result)
        
        return dict(sorted(grouped.items()))
    
    def _generate_stats(self, results: List[Dict]) -> Dict:
        """Generate statistics from results"""
        total = len(results)
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'failed'])
        
        # Count by status code
        status_codes = {}
        for result in results:
            if 'http_status' in result:
                code = result['http_status']
                status_codes[code] = status_codes.get(code, 0) + 1
        
        # Count by source
        sources = {}
        for result in results:
            source = result.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        # Technologies
        technologies = {}
        for result in results:
            if 'technologies' in result:
                for tech in result['technologies']:
                    technologies[tech] = technologies.get(tech, 0) + 1
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            'status_codes': status_codes,
            'sources': sources,
            'technologies': technologies
        }
    
    def _render_html(self, grouped_results: Dict, stats: Dict) -> str:
        """Render HTML template"""
        template_str = self._get_template()
        template = Template(template_str)
        
        return template.render(
            title=self.config['report']['title'],
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            grouped_results=grouped_results,
            stats=stats,
            show_metadata=self.config['report']['show_metadata'],
            theme=self.config['report']['theme']
        )
    
    def _get_template(self) -> str:
        """Get HTML template"""
        return """<!DOCTYPE html>
<html lang="en" data-theme="{{ theme }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --text-primary: #333333;
            --text-secondary: #666666;
            --border-color: #dddddd;
            --accent-color: #0066cc;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
        }
        
        [data-theme="dark"] {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --border-color: #404040;
            --accent-color: #4da3ff;
            --success-color: #4caf50;
            --danger-color: #f44336;
            --warning-color: #ffb300;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: var(--accent-color);
            margin-bottom: 10px;
        }
        
        .timestamp {
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: var(--accent-color);
        }
        
        .domain-section {
            margin-bottom: 40px;
        }
        
        .domain-header {
            background: var(--bg-secondary);
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .domain-header:hover {
            background: var(--border-color);
        }
        
        .domain-name {
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .target-count {
            background: var(--accent-color);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .targets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .target-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .target-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .screenshot-wrapper {
            position: relative;
            width: 100%;
            background: #000;
            overflow: hidden;
        }
        
        .screenshot-wrapper img {
            width: 100%;
            height: auto;
            display: block;
            cursor: pointer;
        }
        
        .status-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-success {
            background: var(--success-color);
            color: white;
        }
        
        .status-failed {
            background: var(--danger-color);
            color: white;
        }
        
        .target-info {
            padding: 15px;
        }
        
        .target-url {
            font-weight: bold;
            margin-bottom: 10px;
            word-break: break-all;
            color: var(--accent-color);
        }
        
        .target-metadata {
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        .metadata-item {
            margin-bottom: 5px;
        }
        
        .metadata-label {
            font-weight: bold;
            margin-right: 5px;
        }
        
        .technologies {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 10px;
        }
        
        .tech-badge {
            background: var(--accent-color);
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
        }
        
        .port-badge {
            background: var(--warning-color);
            color: #000;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 8px;
        }
        
        .discovered-badge {
            background: var(--success-color);
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            margin-left: 5px;
        }
        
        .error-message {
            color: var(--danger-color);
            font-style: italic;
            margin-top: 10px;
        }
        
        /* Modal for full-size images */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }
        
        .modal-content {
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            margin-top: 2%;
        }
        
        .close {
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: #bbb;
        }
        
        .filter-bar {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .filter-bar input,
        .filter-bar select {
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 1em;
        }
        
        .filter-bar input {
            flex: 1;
            min-width: 200px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="timestamp">Generated: {{ timestamp }}</div>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Targets</div>
                <div class="stat-value">{{ stats.total }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Successful</div>
                <div class="stat-value" style="color: var(--success-color);">{{ stats.successful }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Failed</div>
                <div class="stat-value" style="color: var(--danger-color);">{{ stats.failed }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value">{{ stats.success_rate }}</div>
            </div>
        </div>
        
        <div class="filter-bar">
            <input type="text" id="searchInput" placeholder="Search URLs...">
            <select id="statusFilter">
                <option value="">All Status</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
            </select>
        </div>
        
        {% for domain, targets in grouped_results.items() %}
        <div class="domain-section">
            <div class="domain-header">
                <div class="domain-name">{{ domain }}</div>
                <div class="target-count">{{ targets|length }} targets</div>
            </div>
            
            <div class="targets-grid">
                {% for target in targets %}
                <div class="target-card" data-status="{{ target.status }}" data-url="{{ target.url }}">
                    {% if target.status == 'success' and target.screenshots.desktop %}
                    <div class="screenshot-wrapper">
                        <img src="{{ target.screenshots.desktop }}" alt="{{ target.url }}" onclick="openModal(this.src)">
                        <span class="status-badge status-success">{{ target.http_status|default('Success') }}</span>
                    </div>
                    {% else %}
                    <div class="screenshot-wrapper" style="padding: 40px; text-align: center;">
                        <span class="status-badge status-failed">Failed</span>
                        <div style="color: var(--text-secondary);">No screenshot available</div>
                    </div>
                    {% endif %}
                    
                    <div class="target-info">
                        <div class="target-url">
                            {{ target.url }}
                            {% if target.port %}
                            <span class="port-badge">Port {{ target.port }}</span>
                            {% endif %}
                            {% if target.discovered_port %}
                            <span class="discovered-badge">AUTO-DISCOVERED</span>
                            {% endif %}
                        </div>
                        
                        {% if show_metadata %}
                        <div class="target-metadata">
                            {% if target.page_title %}
                            <div class="metadata-item">
                                <span class="metadata-label">Title:</span>
                                {{ target.page_title }}
                            </div>
                            {% endif %}
                            
                            {% if target.http_status %}
                            <div class="metadata-item">
                                <span class="metadata-label">Status:</span>
                                {{ target.http_status }}
                            </div>
                            {% endif %}
                            
                            {% if target.port %}
                            <div class="metadata-item">
                                <span class="metadata-label">Port:</span>
                                {{ target.port }} ({{ target.scheme }})
                            </div>
                            {% endif %}
                            
                            {% if target.source %}
                            <div class="metadata-item">
                                <span class="metadata-label">Source:</span>
                                {{ target.source }}
                            </div>
                            {% endif %}
                            
                            {% if target.technologies %}
                            <div class="technologies">
                                {% for tech in target.technologies %}
                                <span class="tech-badge">{{ tech }}</span>
                                {% endfor %}
                            </div>
                            {% endif %}
                        </div>
                        {% endif %}
                        
                        {% if target.error %}
                        <div class="error-message">Error: {{ target.error }}</div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
    
    <!-- Modal for full-size images -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="close">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>
    
    <script>
        // Image modal
        function openModal(src) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = src;
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }
        
        // Search and filter
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        
        function filterCards() {
            const searchTerm = searchInput.value.toLowerCase();
            const statusValue = statusFilter.value;
            const cards = document.querySelectorAll('.target-card');
            
            cards.forEach(card => {
                const url = card.getAttribute('data-url').toLowerCase();
                const status = card.getAttribute('data-status');
                
                const matchesSearch = url.includes(searchTerm);
                const matchesStatus = !statusValue || status === statusValue;
                
                card.style.display = (matchesSearch && matchesStatus) ? 'block' : 'none';
            });
        }
        
        searchInput.addEventListener('input', filterCards);
        statusFilter.addEventListener('change', filterCards);
        
        // Keyboard shortcut to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>"""


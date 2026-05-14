"""
R1X Platform - Report Generator Module
Professional Security Assessment Reports
Version: 2.0.0
"""

import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# CVSS VECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class CVSSVector:
    """CVSS 3.1 Vector Calculator"""

    # CVSS Base Metrics
    ATTACK_VECTOR = {
        "N": "Network", "A": "Adjacent", "L": "Local", "P": "Physical"
    }
    COMPLEXITY = {
        "H": "High", "L": "Low", "M": "Medium", "N": "Not Defined"
    }
    PRIVILEGES = {
        "H": "High", "L": "Low", "N": "None", "M": "Medium", "N": "Not Defined"
    }
    SCOPE = {
        "C": "Changed", "U": "Unchanged", "N": "Not Defined"
    }
    IMPACT = {
        "H": "High", "L": "Low", "N": "None", "M": "Medium", "X": "Not Defined"
    }

    @classmethod
    def calculate_score(
        cls,
        attack_vector: str = "N",
        complexity: str = "M",
        privileges_required: str = "N",
        user_interaction: str = "N",
        scope: str = "U",
        confidentiality: str = "H",
        integrity: str = "H",
        availability: str = "H"
    ) -> Dict[str, Any]:
        """Calculate CVSS score and rating"""

        base_metrics = [
            attack_vector, complexity, privileges_required,
            user_interaction, scope, confidentiality,
            integrity, availability
        ]

        # Simplified CVSS scoring
        av_score = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}.get(attack_vector[0] if attack_vector else "N", 0.85)
        ac_score = {"H": 0.44, "L": 0.77, "M": 0.62}.get(complexity[0] if complexity else "M", 0.62)
        pr_score = {"H": 0.27, "L": 0.62, "N": 0.85, "M": 0.62}.get(privileges_required[0] if privileges_required else "N", 0.85)
        ui_score = {"N": 0.85, "R": 0.62}.get(user_interaction[0] if user_interaction else "N", 0.85)

        conf_impact = {"N": 0.0, "L": 0.22, "H": 0.56}.get(confidentiality[0] if confidentiality else "N", 0)
        int_impact = {"N": 0.0, "L": 0.22, "H": 0.56}.get(integrity[0] if integrity else "N", 0)
        avai_impact = {"N": 0.0, "L": 0.22, "H": 0.56}.get(availability[0] if availability else "N", 0)

        # Calculate ISS
        iss = 1 - ((1 - conf_impact) * (1 - int_impact) * (1 - avai_impact))

        if scope == "C":
            m = 1.08
        else:
            m = 1.0

        impact = min(1.0, 1.52 * (iss - 0.029)) - 0.02

        if impact <= 0:
            base_score = 0
        else:
            if scope == "C":
                impact = min(1.0, impact + 0.973 * (iss - 0.02))
            base_score = min(10.0, max(0, round(ac_score * pr_score * ui_score + impact, 1)))

        rating = "None"
        if base_score == 0:
            rating = "None"
        elif base_score <= 3.9:
            rating = "Low"
        elif base_score <= 6.9:
            rating = "Medium"
        elif base_score <= 8.9:
            rating = "High"
        else:
            rating = "Critical"

        return {
            "vector": f"CVSS:3.1/AV:{attack_vector}/AC:{complexity}/PR:{privileges_required}/UI:{user_interaction}/S:{scope}/C:{confidentiality}/I:{integrity}/A:{availability}",
            "base_score": base_score,
            "rating": rating
        }


# ═══════════════════════════════════════════════════════════════════════════════
# REMEDIATION DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class RemediationDatabase:
    """Database of remediation steps for common vulnerabilities"""

    # SQL Injection Fix
    SQL_FIX = {
        "title": "SQL Injection Remediation",
        "steps": [
            {
                "action": "Use Parameterized Queries",
                "description": "Replace dynamic SQL construction with parameterized queries (PreparedStatements)",
                "code_snippet": "# Python - Use parameterized queries\nimport pymysql\n\ndef get_user(user_id):\n    conn = pymysql.connect(host='localhost', user='app', password='secret', database='app_db')\n    cursor = conn.cursor()\n    # GOOD - Parameterized query\n    cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))\n    return cursor.fetchone()"
            },
            {
                "action": "Use ORM Framework",
                "description": "Consider using ORM frameworks like SQLAlchemy that automatically handle parameterization",
                "code_snippet": "# Python SQLAlchemy Example\nfrom sqlalchemy import text\n\ndef get_user_orm(session, user_id):\n    result = session.execute(text(\"SELECT * FROM users WHERE id = :id\"), {\"id\": user_id})\n    return result.fetchone()"
            },
            {
                "action": "Implement Input Validation",
                "description": "Validate and sanitize all user inputs before database queries",
                "code_snippet": "import re\n\ndef sanitize_input(user_input):\n    # Remove special SQL characters\n    return re.sub(r'[\\'\"]+', '', user_input)\n\n# Use whitelist validation\nALLOWED_TYPES = {'integer', 'string', 'email'}\ndef validate_type(user_input, input_type):\n    if input_type == 'integer':\n        return str(int(user_input))\n    return user_input"
            }
        ],
        "references": [
            "https://owasp.org/www-community/attacks/SQL_Injection",
            "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
        ]
    }

    # XSS Fix
    XSS_FIX = {
        "title": "Cross-Site Scripting (XSS) Remediation",
        "steps": [
            {
                "action": "Implement Output Encoding",
                "description": "Encode all user input before rendering in HTML pages",
                "code_snippet": "# Python - Use Bleach for HTML sanitization\nfrom bleach import clean\n\ndef sanitize_html(dirty_html):\n    allowed_tags = ['p', 'br', 'b', 'i', 'em', 'strong', 'a']\n    clean_html = clean(dirty_html, tags=allowed_tags, \n                      attributes={'a': ['href', 'title']}, strip=True)\n    return clean_html"
            },
            {
                "action": "Use Security Libraries",
                "description": "Use established security libraries for template rendering",
                "code_snippet": "# Jinja2 Auto-escape\nfrom jinja2 import Markup\n\nclass SafeOutput:\n    def __init__(self, content):\n        self.content = Markup.escape(content)\n    \n    def __html__(self):\n        return self.content"
            }
        ],
        "references": [
            "https://owasp.org/www-community/attacks/xss/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
        ]
    }

    # Path Traversal Fix
    PATH_FIX = {
        "title": "Path Traversal Remediation",
        "steps": [
            {
                "action": "Validate File Paths",
                "description": "Use canonical path validation to prevent directory traversal",
                "code_snippet": "import os\nfrom pathlib import Path\n\ndef safe_read_file(requested_path, base_dir=\"/var/www/uploads\"):\n    base = Path(base_dir).resolve()\n    requested = (base / requested_path).resolve()\n    \n    if not str(requested).startswith(str(base)):\n        raise PermissionError(\"Access denied\")\n    \n    return requested.read_bytes()"
            }
        ],
        "references": [
            "https://owasp.org/www-community/attacks/Path_Traversal",
            "https://cheatsheetseries.owasp.org/cheatsheets/Path_Traversal_Cheat_Sheet.html"
        ]
    }

    # Command Injection Fix
    CMD_FIX = {
        "title": "Command Injection Remediation",
        "steps": [
            {
                "action": "Avoid Shell Commands",
                "description": "Use direct API calls instead of shell commands where possible",
                "code_snippet": "# BAD\nimport os\nos.system(f\"cat {user_input}\")\n\n# GOOD - Use subprocess with list\nimport subprocess\nresult = subprocess.run(['cat', user_input], \n                         capture_output=True, text=True)"
            }
        ],
        "references": [
            "https://owasp.org/www-community/attacks/Command_Injection",
            "https://cheatsheetseries.owasp.org/cheatsheets/Command_Injection_Prevention_Cheat_Sheet.html"
        ]
    }

    def get_remediation(self, vuln_category: str) -> Dict[str, Any]:
        """Get remediation for a vulnerability category"""
        remediation_map = {
            "sql_injection": self.SQL_FIX,
            "xss": self.XSS_FIX,
            "path_traversal": self.PATH_FIX,
            "command_injection": self.CMD_FIX
        }
        return remediation_map.get(vuln_category, {})


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT FORMAT TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ReportFormat(Enum):
    """Supported report formats"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """
    Professional Security Assessment Report Generator

    Features:
    - JSON, HTML, Markdown, CSV output formats
    - CVSS scoring for vulnerabilities
    - Step-by-step remediation guidance
    - Executive summary generation
    - Enumeration results summary
    """

    def __init__(self):
        self.remediation_db = RemediationDatabase()
        self.cvss_calc = CVSSVector()

    async def generate_report(
        self,
        result: Any,
        format_type: str = "json",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive security report"""

        # Build report structure
        report = {
            "scan_id": getattr(result, 'scan_id', 'unknown'),
            "target": getattr(result, 'target', 'unknown'),
            "start_time": getattr(result, 'start_time', time.time()),
            "end_time": getattr(result, 'end_time', time.time()),
            "duration": getattr(result, 'duration', 0),
            "status": getattr(result, 'status', 'unknown'),
            "vulnerabilities": [],
            "summary": {},
            "metadata": {
                "version": "2.0.0",
                "generator": "R1X Platform"
            }
        }

        # Process vulnerabilities
        for vuln in getattr(result, 'vulnerabilities', []):
            vuln_dict = vuln.to_dict() if hasattr(vuln, 'to_dict') else vuln
            vuln_dict['cvss'] = self.cvss_calc.calculate_score()
            report['vulnerabilities'].append(vuln_dict)

        # Calculate summary
        report['summary'] = {
            "total_vulns": len(report['vulnerabilities']),
            "critical": sum(1 for v in report['vulnerabilities'] if v.get('severity') == 'critical'),
            "high": sum(1 for v in report['vulnerabilities'] if v.get('severity') == 'high'),
            "medium": sum(1 for v in report['vulnerabilities'] if v.get('severity') == 'medium'),
            "low": sum(1 for v in report['vulnerabilities'] if v.get('severity') == 'low'),
            "risk_score": getattr(result, 'risk_score', 0)
        }

        # Get remediation for each vulnerability
        for vuln in report['vulnerabilities']:
            category = vuln.get('category', '').lower()
            if 'sql' in category or 'injection' in category:
                vuln['remediation'] = self.remediation_db.SQL_FIX
            elif 'xss' in category or 'script' in category:
                vuln['remediation'] = self.remediation_db.XSS_FIX
            elif 'path' in category or 'traversal' in category:
                vuln['remediation'] = self.remediation_db.PATH_FIX
            elif 'command' in category or 'injection' in category:
                vuln['remediation'] = self.remediation_db.CMD_FIX

        # Add enumeration results
        report['enumeration_results'] = {
            "endpoints": getattr(result, 'endpoints', []),
            "files_found": getattr(result, 'files_found', []),
            "technologies": getattr(result, 'technologies', []),
            "waf_detected": getattr(result, 'waf_detected', None)
        }

        # Format report
        output_file = output_file or f"r1x_report_{result.scan_id}.{format_type}"

        if format_type == "json":
            content = self._format_json(report)
        elif format_type == "html":
            content = self._format_html(report)
        elif format_type == "markdown":
            content = self._format_markdown(report)
        elif format_type == "csv":
            content = self._format_csv(report)
        else:
            content = self._format_json(report)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "format": format_type,
            "output_file": output_file,
            "vulnerabilities_found": len(report['vulnerabilities']),
            "summary": report['summary']
        }

    def _format_json(self, report: Dict[str, Any]) -> str:
        """Format report as JSON"""
        return json.dumps(report, indent=2, default=str)

    def _format_html(self, report: Dict[str, Any]) -> str:
        """Format report as HTML"""
        critical = report['summary'].get('critical', 0)
        high = report['summary'].get('high', 0)
        medium = report['summary'].get('medium', 0)
        low = report['summary'].get('low', 0)
        total = report['summary'].get('total_vulns', 0)

        vuln_rows = ""
        for v in report.get('vulnerabilities', []):
            remediation = v.get('remediation', {})
            steps_html = ""
            for step in remediation.get('steps', []):
                steps_html += f"<li><strong>{step.get('action', '')}</strong>: {step.get('description', '')}</li>"
                if step.get('code_snippet'):
                    steps_html += f"<pre><code>{step.get('code_snippet', '')}</code></pre>"

            vuln_rows += f"""
            <div class=\"vuln-card\">
                <h3>{v.get('title', 'Unknown Vulnerability')}</h3>
                <span class=\"severity {v.get('severity', 'info')}\">{v.get('severity', 'info').upper()}</span>
                <p><strong>URL:</strong> {v.get('url', 'N/A')}</p>
                <p><strong>CVSS:</strong> {v.get('cvss', {}).get('base_score', 'N/A')} ({v.get('cvss', {}).get('rating', 'N/A')})</p>
                <p>{v.get('description', '')}</p>
                <h4>Remediation:</h4>
                <ol>{steps_html}</ol>
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>R1X Security Report - {report.get('target', 'Unknown')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); color: white; padding: 30px; border-radius: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card.critical {{ border-left: 4px solid #dc2626; }}
        .summary-card.high {{ border-left: 4px solid #f59e0b; }}
        .summary-card.medium {{ border-left: 4px solid #fbbf24; }}
        .summary-card.low {{ border-left: 4px solid #10b981; }}
        .vuln-card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .severity {{ padding: 4px 12px; border-radius: 4px; font-weight: bold; }}
        .severity.critical {{ background: #dc2626; color: white; }}
        .severity.high {{ background: #f59e0b; color: white; }}
        .severity.medium {{ background: #fbbf24; }}
        .severity.low {{ background: #10b981; color: white; }}
        pre {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        h3 {{ margin-top: 0; color: #1e3a5f; }}
        li {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div class=\"header\">
        <h1>R1X Security Assessment Report</h1>
        <p><strong>Target:</strong> {report.get('target', 'Unknown')}</p>
        <p><strong>Scan ID:</strong> {report.get('scan_id', 'N/A')}</p>
        <p><strong>Generated:</strong> {report.get('end_time', time.time())}</p>
    </div>

    <h2>Summary</h2>
    <div class=\"summary\">
        <div class=\"summary-card critical\">
            <h3>{critical}</h3>
            <p>Critical</p>
        </div>
        <div class=\"summary-card high\">
            <h3>{high}</h3>
            <p>High</p>
        </div>
        <div class=\"summary-card medium\">
            <h3>{medium}</h3>
            <p>Medium</p>
        </div>
        <div class=\"summary-card low\">
            <h3>{low}</h3>
            <p>Low</p>
        </div>
        <div class=\"summary-card\">
            <h3>{total}</h3>
            <p>Total</p>
        </div>
    </div>

    <h2>Vulnerabilities</h2>
    {vuln_rows}

    <footer style=\"margin-top: 40px; text-align: center; color: #666;\">
        <p>Generated by R1X Platform v2.0.0</p>
    </footer>
</body>
</html>
        """
        return html

    def _format_markdown(self, report: Dict[str, Any]) -> str:
        """Format report as Markdown"""
        critical = report['summary'].get('critical', 0)
        high = report['summary'].get('high', 0)
        medium = report['summary'].get('medium', 0)
        low = report['summary'].get('low', 0)
        total = report['summary'].get('total_vulns', 0)

        md = f"""# R1X Security Assessment Report

## Target Information

| Property | Value |
|----------|-------|
| **Target** | {report.get('target', 'Unknown')} |
| **Scan ID** | {report.get('scan_id', 'N/A')} |
| **Duration** | {report.get('duration', 0):.2f}s |
| **Status** | {report.get('status', 'Unknown')} |

## Summary

| Severity | Count |
|----------|-------|
| Critical | {critical} |
| High | {high} |
| Medium | {medium} |
| Low | {low} |
| **Total** | **{total}** |

## Enumeration Results

**Endpoints Found:** {len(report.get('enumeration_results', {}).get('endpoints', []))}
**Files Found:** {len(report.get('enumeration_results', {}).get('files_found', []))}
**Technologies:** {', '.join(report.get('enumeration_results', {}).get('technologies', [])) or 'None detected'}
**WAF Detected:** {report.get('enumeration_results', {}).get('waf_detected', 'None')}

## Vulnerabilities

"""

        for v in report.get('vulnerabilities', []):
            cvss = v.get('cvss', {})
            remediation = v.get('remediation', {})

            md += f"""### {v.get('title', 'Unknown')}

- **Severity:** {v.get('severity', 'info').upper()}
- **CVSS Score:** {cvss.get('base_score', 'N/A')} ({cvss.get('rating', 'N/A')})
- **URL:** {v.get('url', 'N/A')}
- **Category:** {v.get('category', 'N/A')}

**Description:**
{v.get('description', 'No description available')}

"""

            if remediation.get('steps'):
                md += "**Remediation:**\n\n"
                for i, step in enumerate(remediation.get('steps', []), 1):
                    md += f"{i}. **{step.get('action', '')}**\n   - {step.get('description', '')}\n"
                    if step.get('code_snippet'):
                        md += f"```\n{step.get('code_snippet', '')}\n```\n"

            md += "---\n\n"

        md += """
---
*Report generated by R1X Platform v2.0.0*
"""
        return md

    def _format_csv(self, report: Dict[str, Any]) -> str:
        """Format vulnerabilities as CSV"""
        import csv
        from io import StringIO

        output = StringIO()
        fieldnames = ['vuln_id', 'title', 'category', 'severity', 'cvss_score',
                      'cvss_rating', 'url', 'cwe_id']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for v in report.get('vulnerabilities', []):
            cvss = v.get('cvss', {})
            writer.writerow({
                'vuln_id': v.get('vuln_id', ''),
                'title': v.get('title', ''),
                'category': v.get('category', ''),
                'severity': v.get('severity', 'info'),
                'cvss_score': cvss.get('base_score', 0),
                'cvss_rating': cvss.get('rating', 'N/A'),
                'url': v.get('url', ''),
                'cwe_id': v.get('cwe_id', '')
            })

        return output.getvalue()

    def generate_executive_summary(self, report: Dict[str, Any]) -> str:
        """Generate executive summary text"""
        total = report['summary'].get('total_vulns', 0)
        critical = report['summary'].get('critical', 0)
        high = report['summary'].get('high', 0)

        if total == 0:
            return "No vulnerabilities were detected during this assessment."

        risk_level = "Critical"
        if critical == 0:
            if high > 0:
                risk_level = "High"
            else:
                risk_level = "Medium"

        summary = f"""
## Executive Summary

**Target:** {report.get('target', 'Unknown')}
**Assessment Date:** {report.get('end_time', 'N/A')}
**Risk Level:** {risk_level}

### Overview

A security assessment was conducted on the target system. The assessment
identified **{total}** potential vulnerabilities:

- Critical: **{critical}**
- High: **{high}**
- Medium: **{report['summary'].get('medium', 0)}**
- Low: **{report['summary'].get('low', 0)}**

### Recommendations

"""

        if critical > 0:
            summary += "1. **Immediate Action Required** - Critical vulnerabilities must be addressed immediately.\n"
        if high > 0:
            summary += "2. **High Priority** - High severity issues should be scheduled for immediate remediation.\n"

        summary += "\nPlease review the detailed findings below and implement the recommended remediation steps.\n"

        return summary
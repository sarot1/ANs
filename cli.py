"""
R1X Platform - CLI Interface
Command-Line Interface for R1X Cyber Intelligence Platform
Version: 2.0.0

واجهة الأوامر:
- فحص شامل بأمر واحد
- خيارات متعددة للتحكم
- عرض النتائج بشكل جميل
- تصدير التقارير
"""

import asyncio
import sys
import argparse
from typing import Optional
from pathlib import Path

from core.constants import VERSION, ScanType, ScanStatus
from core.exceptions import R1XException
from orchestrator.central_orchestrator import CentralOrchestrator, ScanConfig
from reports.report_generator import ReportGenerator


# ═══════════════════════════════════════════════════════════════════════════════
# ANSI COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def c(color: str, text: str) -> str:
    """Apply color to text"""
    return f"{color}{text}{Colors.RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CLI
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="r1x",
        description=c(Colors.CYAN, "R1X - Autonomous Cyber Intelligence Platform"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{c(Colors.GREEN, "Examples:")}

  {c(Colors.CYAN, "# Full scan with all features")}
  r1x scan https://example.com

  {c(Colors.CYAN, "# Quick scan, skip enumeration")}
  r1x scan https://example.com --type quick --no-enumeration

  {c(Colors.CYAN, "# Scan with custom concurrency")}
  r1x scan https://example.com -c 100

  {c(Colors.CYAN, "# Scan and save report")}
  r1x scan https://example.com --output report.json

  {c(Colors.CYAN, "# HTML report with remediation")}
  r1x scan https://example.com --format html --output report.html

  {c(Colors.CYAN, "# Verbose mode")}
  r1x scan https://example.com -v

  {c(Colors.CYAN, "# Show version")}
  r1x --version

{c(Colors.YELLOW, "Note:")} This tool is for authorized security testing only.
        """
    )

    # Version
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"r1x {VERSION}"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Execute security scan")
    scan_parser.add_argument(
        "target",
        help="Target URL to scan"
    )
    scan_parser.add_argument(
        "--type", "-t",
        choices=["full", "quick", "deep", "recon", "enum"],
        default="full",
        help="Scan type (default: full)"
    )
    scan_parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=50,
        help="Max concurrent requests (default: 50)"
    )
    scan_parser.add_argument(
        "--timeout", "-T",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30)"
    )
    scan_parser.add_argument(
        "--bypass-attempts", "-b",
        type=int,
        default=9,
        help="Max bypass attempts (default: 9)"
    )
    scan_parser.add_argument(
        "--no-recon",
        action="store_true",
        help="Skip reconnaissance phase"
    )
    scan_parser.add_argument(
        "--no-enumeration",
        action="store_true",
        help="Skip enumeration phase"
    )
    scan_parser.add_argument(
        "--no-vuln-scan",
        action="store_true",
        help="Skip vulnerability scanning"
    )
    scan_parser.add_argument(
        "--output", "-o",
        help="Output file path"
    )
    scan_parser.add_argument(
        "--format", "-f",
        choices=["json", "html", "markdown"],
        default="json",
        help="Report format (default: json)"
    )
    scan_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    scan_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (minimal output)"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show platform information")
    info_parser.add_argument(
        "--components",
        action="store_true",
        help="Show installed components"
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "scan" or args.command is None:
        if args.command is None and len(sys.argv) > 1:
            # Assume scan command if no subcommand but target is provided
            args.command = "scan"
            if not hasattr(args, 'target'):
                args.target = sys.argv[1] if len(sys.argv) > 1 else None
                args.type = "full"
                args.concurrency = 50
                args.timeout = 30.0
                args.bypass_attempts = 9
                args.no_recon = False
                args.no_enumeration = False
                args.no_vuln_scan = False
                args.output = None
                args.format = "json"
                args.verbose = False
                args.quiet = False

        if args.command == "scan":
            await run_scan(args)
        else:
            parser.print_help()

    elif args.command == "info":
        show_info(args)

    else:
        parser.print_help()


async def run_scan(args):
    """Execute scan command"""
    # Validate target
    if not args.target:
        print(c(Colors.RED, "Error: Target URL is required"))
        sys.exit(1)

    # Map scan types
    type_map = {
        "full": ScanType.FULL_SCAN,
        "quick": ScanType.QUICK_SCAN,
        "deep": ScanType.DEEP_SCAN,
        "recon": ScanType.RECON,
        "enum": ScanType.ENUMERATION
    }

    # Create scan config
    config = ScanConfig(
        target=args.target,
        scan_type=type_map.get(args.type, ScanType.FULL_SCAN),
        max_concurrency=args.concurrency,
        timeout=args.timeout,
        max_bypass_attempts=args.bypass_attempts,
        include_recon=not args.no_recon,
        include_enumeration=not args.no_enumeration,
        include_vuln_scan=not args.no_vuln_scan,
        output_format=args.format,
        output_file=args.output,
        verbose=not args.quiet
    )

    # Print banner
    if not args.quiet:
        print_banner()

    try:
        # Initialize orchestrator
        orchestrator = CentralOrchestrator(config)
        await orchestrator.initialize()

        # Execute scan
        print(c(Colors.CYAN, f"\n🎯 Starting scan on: {args.target}\n"))

        result = await orchestrator.execute_scan()

        # Print summary
        if not args.quiet:
            print_scan_summary(result)

        # Generate report
        if args.output or args.format != "json":
            report_gen = ReportGenerator(result)
            output_file = args.output or f"r1x_report_{result.scan_id}.{args.format}"

            report = await report_gen.generate(
                format=args.format,
                output_file=output_file
            )

            if not args.quiet:
                print(c(Colors.GREEN, f"\n✅ Report saved to: {output_file}\n"))

        # Cleanup
        await orchestrator.cleanup()

        # Exit code based on vulnerabilities
        if result.vuln_summary.get("critical", 0) > 0:
            sys.exit(2)  # Critical vulnerabilities found
        elif result.vuln_summary.get("high", 0) > 0:
            sys.exit(1)  # High vulnerabilities found

    except KeyboardInterrupt:
        print(c(Colors.YELLOW, "\n⚠️  Scan interrupted by user"))
        sys.exit(130)

    except R1XException as e:
        print(c(Colors.RED, f"\n❌ Error: {e.message}"))
        sys.exit(1)

    except Exception as e:
        print(c(Colors.RED, f"\n❌ Unexpected error: {str(e)}"))
        sys.exit(1)


def print_banner():
    """Print R1X banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██╗   ██╗ ██████╗ ██████╗ ████████╗ ██████╗ ██████╗ ██╗   ██╗  ║
    ║   ╚██╗ ██╔╝██╔═══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗██║   ██║  ║
    ║    ╚████╔╝ ██║   ██║██████╔╝   ██║   ██║   ██║██████╔╝██║   ██║  ║
    ║     ╚██╔╝  ██║   ██║██╔══██╗   ██║   ██║   ██║██╔══██╗██║   ██║  ║
    ║      ██║   ╚██████╔╝██║  ██║   ██║   ╚██████╔╝██║  ██║╚██████╔╝  ║
    ║      ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ║
    ║                                                               ║
    ║   {Colors.RESET}Autonomous Cyber Intelligence Platform{Colors.CYAN}{Colors.BOLD}                ║
    ║   Version {VERSION}{' ' * (40 - len(VERSION))} ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
    print(banner)


def print_scan_summary(result):
    """Print scan summary"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(c(Colors.BOLD, "📊 SCAN RESULTS"))
    print(f"{'='*70}\n")

    # Status
    status_color = Colors.GREEN if result.status == "completed" else Colors.RED
    print(f"   Status: {c(status_color, result.status.upper())}")
    print(f"   Duration: {result.duration:.2f}s" if result.duration else "   Duration: N/A")
    print()

    # Risk score
    risk_score = result.risk_score
    if risk_score >= 7:
        risk_color = Colors.RED
        risk_label = "CRITICAL"
    elif risk_score >= 4:
        risk_color = Colors.YELLOW
        risk_label = "HIGH"
    else:
        risk_color = Colors.GREEN
        risk_label = "LOW"

    print(f"   Risk Score: {c(risk_color, f'{risk_score:.1f}/10')} ({risk_label})")
    print()

    # Vulnerabilities by severity
    print(f"   {c(Colors.BOLD, 'Vulnerabilities:')}")
    summary = result.vuln_summary

    vuln_counts = [
        ("Critical", summary.get("critical", 0), Colors.RED),
        ("High", summary.get("high", 0), Colors.YELLOW),
        ("Medium", summary.get("medium", 0), Colors.CYAN),
        ("Low", summary.get("low", 0), Colors.GREEN),
        ("Info", summary.get("info", 0), Colors.DIM)
    ]

    for label, count, color in vuln_counts:
        if count > 0:
            print(f"      {c(color, '●')} {label}: {c(color, str(count))}")

    if sum(summary.values()) == 0:
        print(f"      {c(Colors.GREEN, '● No vulnerabilities found')}")

    print()

    # Bypass results
    if result.bypass_attempts > 0:
        print(f"   {c(Colors.BOLD, 'WAF Bypass:')}")
        if result.bypass_successful:
            print(f"      {c(Colors.GREEN, '✓')} Successful after {result.bypass_attempts} attempts")
        else:
            print(f"      {c(Colors.RED, '✗')} All {result.bypass_attempts} attempts blocked")

    if result.waf_detected:
        print(f"      WAF Detected: {c(Colors.YELLOW, result.waf_detected)}")

    print()

    # Enumeration results
    print(f"   {c(Colors.BOLD, 'Enumeration:')}")
    print(f"      Endpoints: {len(result.endpoints)}")
    print(f"      Files: {len(result.files_found)}")
    print(f"      Technologies: {', '.join(result.technologies[:5])}" if result.technologies else "      None detected")

    print(f"\n{'='*70}\n")


def show_info(args):
    """Show platform information"""
    print(f"\n{c(Colors.CYAN, 'R1X Platform Information')}\n")
    print(f"   Version: {VERSION}")
    print(f"   Platform: Autonomous Cyber Intelligence")
    print(f"   Python: {sys.version.split()[0]}")
    print()

    if hasattr(args, 'components') and args.components:
        print(c(Colors.BOLD, "   Components:"))
        components = [
            ("Core", "Base system components"),
            ("HTTP Client", "Async HTTP with connection pool"),
            ("Bypass Engine", "WAF bypass with persistent retry"),
            ("Memory Graph", "Knowledge persistence"),
            ("Telemetry", "Performance monitoring"),
            ("Report Generator", "Professional reports"),
            ("CLI", "Command-line interface")
        ]
        for name, desc in components:
            print(f"      • {c(Colors.CYAN, name)}: {desc}")

    print()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def entry_point():
    """Entry point for console script"""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())

"""
██╗    ██╗██╗  ██╗██╗███████╗██████╗  █████╗ ███████╗███╗   ███╗
██║    ██║██║ ██╔╝██║██╔════╝██╔══██╗██╔══██╗██╔════╝████╗ ████║
██║ █╗ ██║█████╔╝ ██║█████╗  ██████╔╝███████║███████╗██╔████╔██║
██║███╗██║██╔═██╗ ██║██╔══╝  ██╔══██╗██╔══██║╚════██║██║╚██╔╝██║
╚███╔███╔╝██║  ██╗██║███████╗██║  ██║██║  ██║███████║██║ ╚═╝ ██║
 ╚══╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝
 Autonomous Cyber Intelligence Platform v3.0.0
 DeepSeek AI + Telegram Integration
"""

import asyncio
import os
import sys
import argparse
from typing import Optional

from core.constants import VERSION, ScanType
from orchestrator.central_orchestrator import CentralOrchestrator, ScanConfig
from reports.report_generator import ReportGenerator
from cli.cli import CLI, console, print_banner
from api.brain import create_brain, VIPX1Brain


class VIPX1Platform:
    """Main Platform Entry Point - With DeepSeek AI & Telegram Bot"""

    def __init__(self):
        self.orchestrator: Optional[CentralOrchestrator] = None
        self.brain: Optional[VIPX1Brain] = None
        self.cli = CLI()

    async def initialize_brain(
        self,
        deepseek_api_key: Optional[str] = None,
        telegram_bot_token: Optional[str] = None
    ) -> None:
        """Initialize the Brain with DeepSeek AI and Telegram"""
        # Get API keys from environment if not provided
        deepseek_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        telegram_token = telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")

        if deepseek_key or telegram_token:
            self.brain = await create_brain(
                deepseek_api_key=deepseek_key,
                telegram_bot_token=telegram_token,
                auto_bypass=True,
                auto_update_telegram=True
            )
            console.print("[green]✅ Brain initialized with DeepSeek AI[/green]")
        else:
            console.print("[yellow]⚠️  No API keys provided - running in basic mode[/yellow]")

    async def run_scan(
        self,
        target: str,
        scan_type: ScanType = ScanType.FULL_SCAN,
        max_concurrency: int = 50,
        max_bypass: int = 9,
        output_format: str = "json",
        output_file: Optional[str] = None,
        verbose: bool = True
    ) -> None:
        """Execute a vulnerability scan with AI assistance"""

        # Create configuration
        config = ScanConfig(
            target=target,
            scan_type=scan_type,
            max_concurrency=max_concurrency,
            max_bypass_attempts=max_bypass,
            output_format=output_format,
            output_file=output_file,
            verbose=verbose
        )

        # Initialize orchestrator
        self.orchestrator = CentralOrchestrator(config)
        await self.orchestrator.initialize()

        # Connect Brain to Bypass Engine if available
        if self.brain and self.orchestrator.bypass_engine:
            self.orchestrator.bypass_engine.set_brain(self.brain)
            console.print("[green]🔗 Brain connected to Bypass Engine[/green]")

        try:
            # Execute scan
            print_banner()
            result = await self.orchestrator.execute_scan()

            # Update Brain with scan results
            if self.brain and result.scan_id:
                await self.brain.complete_scan(
                    scan_id=result.scan_id,
                    results={
                        "vulnerabilities": [v.to_dict() for v in result.vulnerabilities],
                        "endpoints": result.endpoints,
                        "files": result.files_found
                    },
                    success=True
                )

            # Generate report
            if verbose:
                print("\n" + "="*70)
                print("📊 Generating Report...")
                print("="*70 + "\n")

            report_gen = ReportGenerator()
            report = await report_gen.generate_report(
                result=result,
                format_type=output_format,
                output_file=output_file
            )

            if verbose:
                console.print(f"\n✅ Scan completed!")
                console.print(f"   Report saved to: {report['output_file']}")
                console.print(f"   Vulnerabilities found: {len(result.vulnerabilities)}")
                if result.bypass_successful:
                    console.print(f"   ⚡ WAF Bypass: Successful ({result.bypass_attempts} attempts)")
                    if self.brain:
                        console.print(f"   🤖 AI Bypass: Enhanced mode")
                else:
                    console.print(f"   🔒 WAF Bypass: Not required")

            return result

        except Exception as e:
            console.print(f"\n❌ Scan failed: {e}", style="bold red")
            raise
        finally:
            await self.orchestrator.cleanup()

    async def list_agents(self) -> None:
        """Display available agents"""
        agents = [
            ("Recon Agent", "Reconnaissance & Fingerprinting"),
            ("Scanner Agent", "Vulnerability Detection"),
            ("Intelligence Agent", "Threat Analysis"),
            ("DeepSeek Agent", "AI-Powered Analysis ⭐"),
            ("Bypass Agent", "WAF Bypass with AI ⭐"),
            ("Performance Agent", "Optimization & Concurrency"),
            ("Stealth Agent", "WAF Bypass & Evasion"),
            ("Telemetry Agent", "Monitoring & Metrics"),
            ("Anomaly Agent", "Behavioral Analysis"),
            ("Optimizer Agent", "Resource Management"),
            ("Remediation Agent", "Report Generation")
        ]

        print_banner()
        console.print("\n🕵️  Available Agents:")
        console.print("-" * 50)

        for name, desc in agents:
            console.print(f"  • {name:20s} - {desc}")

        console.print("\n")

    async def get_status(self) -> dict:
        """Get platform status"""
        status = {"status": "idle", "version": VERSION}

        if self.orchestrator:
            orch_status = await self.orchestrator.get_status()
            status.update(orch_status)

        if self.brain:
            brain_stats = self.brain.get_statistics()
            status["brain"] = brain_stats
            status["deepseek"] = brain_stats.get("deepseek", {})

        return status

    async def start_telegram_bot(self) -> None:
        """Start the Telegram bot for remote control"""
        if not self.brain or not self.brain.telegram:
            console.print("[red]❌ Telegram bot not initialized[/red]")
            console.print("   Provide TELEGRAM_BOT_TOKEN environment variable")
            return

        console.print("[green]🤖 Starting Telegram Bot...[/green]")
        console.print("[yellow]   Use /help in Telegram to see available commands[/yellow]")

        try:
            await self.brain.telegram.start()
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Telegram bot stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Telegram bot error: {e}[/red]")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog="vipx1",
        description="VIPX1 - Autonomous Cyber Intelligence Platform with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vipx1 scan https://example.com
  vipx1 scan https://example.com --type quick_scan
  vipx1 scan https://example.com --format html --output report.html
  vipx1 agents
  vipx1 status
  vipx1 bot  # Start Telegram bot

Environment Variables:
  DEEPSEEK_API_KEY   - Your DeepSeek API key for AI assistance
  TELEGRAM_BOT_TOKEN - Your Telegram bot token for remote control
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Execute vulnerability scan")
    scan_parser.add_argument("target", help="Target URL (e.g., https://example.com)")
    scan_parser.add_argument(
        "--type", "-t",
        dest="scan_type",
        choices=["full_scan", "quick_scan", "deep_scan", "recon", "vuln_scan", "enumeration"],
        default="full_scan",
        help="Scan type (default: full_scan)"
    )
    scan_parser.add_argument(
        "--concurrency", "-c",
        dest="max_concurrency",
        type=int,
        default=50,
        help="Max concurrent requests (default: 50)"
    )
    scan_parser.add_argument(
        "--max-bypass", "-b",
        dest="max_bypass",
        type=int,
        default=9,
        help="Max bypass attempts (default: 9)"
    )
    scan_parser.add_argument(
        "--format", "-f",
        dest="output_format",
        choices=["json", "html", "markdown", "csv"],
        default="json",
        help="Report format (default: json)"
    )
    scan_parser.add_argument(
        "--output", "-o",
        dest="output_file",
        help="Output file path"
    )
    scan_parser.add_argument(
        "--quiet", "-q",
        dest="verbose",
        action="store_false",
        help="Quiet mode (less output)"
    )

    # Agents command
    agents_parser = subparsers.add_parser("agents", help="List available agents")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show platform status")

    # Bot command
    bot_parser = subparsers.add_parser("bot", help="Start Telegram bot")

    # Version
    parser.add_argument("--version", "-v", action="version", version=f"VIPX1 v{VERSION}")

    return parser.parse_args()


async def main_async(args: argparse.Namespace) -> int:
    """Main async entry point"""

    # Handle commands
    if args.command == "scan":
        # Parse scan type
        scan_type_map = {
            "full_scan": ScanType.FULL_SCAN,
            "quick_scan": ScanType.QUICK_SCAN,
            "deep_scan": ScanType.DEEP_SCAN,
            "recon": ScanType.RECON,
            "vuln_scan": ScanType.VULN_SCAN,
            "enumeration": ScanType.ENUMERATION
        }
        scan_type = scan_type_map.get(args.scan_type, ScanType.FULL_SCAN)

        # Create and run platform
        platform = VIPX1Platform()

        # Initialize Brain with API keys
        await platform.initialize_brain()

        try:
            await platform.run_scan(
                target=args.target,
                scan_type=scan_type,
                max_concurrency=args.max_concurrency,
                max_bypass=args.max_bypass,
                output_format=args.output_format,
                output_file=args.output_file,
                verbose=args.verbose
            )
        except KeyboardInterrupt:
            console.print("\n\n⚠️  Scan interrupted by user", style="bold yellow")
            return 130  # SIGINT
        except Exception as e:
            console.print(f"\n\n❌ Fatal error: {e}", style="bold red")
            return 1
        finally:
            if platform.brain:
                await platform.brain.cleanup()

    elif args.command == "agents":
        platform = VIPX1Platform()
        await platform.list_agents()

    elif args.command == "status":
        platform = VIPX1Platform()
        await platform.initialize_brain()
        status = await platform.get_status()

        console.print(f"\n📡 Platform Status: {status.get('status', 'unknown')}")
        console.print(f"   Version: {VERSION}")

        if "deepseek" in status:
            ds = status["deepseek"]
            console.print(f"\n🤖 DeepSeek AI:")
            console.print(f"   Requests: {ds.get('requests_total', 0)}")
            console.print(f"   Success: {ds.get('requests_success', 0)}")
            console.print(f"   Cached: {ds.get('requests_cached', 0)}")

        if platform.brain:
            await platform.brain.cleanup()

    elif args.command == "bot":
        platform = VIPX1Platform()
        await platform.initialize_brain()
        await platform.start_telegram_bot()
        if platform.brain:
            await platform.brain.cleanup()

    else:
        # No command provided, show banner
        print_banner()
        console.print("\n📖 Usage: vipx1 <command> [options]\n")
        console.print("Commands:")
        console.print("  scan    - Execute vulnerability scan")
        console.print("  agents  - List available agents")
        console.print("  status  - Show platform status")
        console.print("  bot     - Start Telegram bot")
        console.print("\nType 'vipx1 <command> --help' for more information.\n")

    return 0


def main() -> int:
    """Main entry point"""
    import uvloop

    # Use uvloop for better performance
    uvloop.install()

    # Parse arguments
    args = parse_arguments()

    # Handle idle (no command)
    if not args.command:
        print_banner()
        console.print("\n📖 Usage: vipx1 <command> [options]\n")
        console.print("Commands:")
        console.print("  scan    - Execute vulnerability scan")
        console.print("  agents  - List available agents")
        console.print("  status  - Show platform status")
        console.print("  bot     - Start Telegram bot")
        console.print("\nEnvironment Variables:")
        console.print("  DEEPSEEK_API_KEY   - DeepSeek API key")
        console.print("  TELEGRAM_BOT_TOKEN - Telegram bot token")
        console.print("\nType 'vipx1 <command> --help' for more information.\n")
        return 0

    # Run async main
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console.print("\n\n⚠️  Interrupted by user", style="bold yellow")
        return 130


if __name__ == "__main__":
    sys.exit(main())
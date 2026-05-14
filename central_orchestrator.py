"""
R1X Platform - Central Orchestrator
The Brain of R1X - Coordinates All Components
Version: 2.0.0

المُنسق المركزي للنظام:
- يدير جميع العمليات
- يُوزع المهام على agents
- يتابع الأداء
- يربط بين Memory, Telemetry, Bypass Engine
- يُنتج التقارير النهائية
"""

import asyncio
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from core.constants import (
    VERSION, ScanType, ScanStatus, Limits, Timeouts
)
from core.base_classes import Task, ScanResult, Vulnerability
from core.exceptions import ScanError, TaskFailedError
from memory.knowledge_graph import KnowledgeGraph, SessionMemory
from telemetry.telemetry_hub import TelemetryHub
from modules.network.http_client import HTTPClient, RequestConfig, WAFDetector, ResponseState
from modules.network.bypass_engine import WAFBypassEngine, BypassContext, BypassResult, BlockType
from modules.network.http_client import HTTPResponse


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ScanConfig:
    """Configuration for a scan operation"""
    target: str
    scan_type: ScanType = ScanType.FULL_SCAN
    max_concurrency: int = Limits.MAX_CONCURRENT_REQUESTS
    timeout: float = Timeouts.TOTAL
    max_bypass_attempts: int = 9
    include_recon: bool = True
    include_enumeration: bool = True
    include_vuln_scan: bool = True
    output_format: str = "json"
    output_file: Optional[str] = None
    verbose: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "scan_type": self.scan_type.value,
            "max_concurrency": self.max_concurrency,
            "timeout": self.timeout,
            "max_bypass_attempts": self.max_bypass_attempts,
            "include_recon": self.include_recon,
            "include_enumeration": self.include_enumeration,
            "include_vuln_scan": self.include_vuln_scan,
            "output_format": self.output_format
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR STATE
# ═══════════════════════════════════════════════════════════════════════════════

class OrchestratorState(Enum):
    """Orchestrator state"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    SCANNING = "scanning"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


# ═══════════════════════════════════════════════════════════════════════════════
# CENTRAL ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class CentralOrchestrator:
    """
    🧠 الدماغ المركزي - Central Orchestrator

    ينسق جميع مكونات R1X:
    - HTTP Client (الاتصالات)
    - Bypass Engine (تجاوز الحمايات)
    - Memory Graph (التخزين والتعلم)
    - Telemetry Hub (المراقبة)
    - Report Generator (التقارير)

    workflow:
    1. Initialize all components
    2. Create scan context
    3. Execute scan phases in sequence
    4. Monitor and adapt in real-time
    5. Store results in memory
    6. Generate final report
    """

    def __init__(self, config: Optional[ScanConfig] = None):
        # Configuration
        self.config = config or ScanConfig(target="")

        # State
        self.state = OrchestratorState.IDLE
        self.scan_id = ""
        self.scan_start_time = 0.0

        # Components
        self.http_client: Optional[HTTPClient] = None
        self.bypass_engine: Optional[WAFBypassEngine] = None
        self.knowledge_graph: Optional[KnowledgeGraph] = None
        self.telemetry: Optional[TelemetryHub] = None

        # Session
        self.session: Optional[SessionMemory] = None

        # Results
        self.scan_result: Optional[ScanResult] = None
        self.scan_progress = 0.0
        self.scan_phase = ""

        # Callbacks
        self._progress_callbacks: List[Callable] = []

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    async def initialize(self) -> None:
        """Initialize all components"""
        self.state = OrchestratorState.INITIALIZING

        # Generate scan ID
        self.scan_id = hashlib.sha256(
            f"{self.config.target}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Initialize HTTP client
        self.http_client = HTTPClient(
            max_connections=self.config.max_concurrency,
            timeout=self.config.timeout
        )
        await self.http_client.initialize()

        # Initialize bypass engine
        self.bypass_engine = WAFBypassEngine(self.http_client)

        # Initialize knowledge graph
        self.knowledge_graph = KnowledgeGraph()

        # Create session
        self.session = await self.knowledge_graph.create_session(
            session_id=self.scan_id,
            target=self.config.target,
            scan_type=self.config.scan_type.value
        )

        # Initialize telemetry
        self.telemetry = TelemetryHub()
        await self.telemetry.start()

        # Initialize scan result
        self.scan_result = ScanResult(
            scan_id=self.scan_id,
            target=self.config.target,
            start_time=time.time(),
            status=ScanStatus.RUNNING.value
        )

        self.state = OrchestratorState.IDLE

        if self.config.verbose:
            print(f"\n{'='*70}")
            print(f"🚀 R1X Platform v{VERSION} - Initializing Scan")
            print(f"{'='*70}")
            print(f"   Scan ID: {self.scan_id}")
            print(f"   Target: {self.config.target}")
            print(f"   Scan Type: {self.config.scan_type.value}")
            print(f"   Max Concurrency: {self.config.max_concurrency}")
            print(f"{'='*70}\n")

    async def cleanup(self) -> None:
        """Cleanup all resources"""
        if self.http_client:
            await self.http_client.cleanup()

        if self.telemetry:
            await self.telemetry.stop()

        if self.knowledge_graph:
            await self.knowledge_graph.cleanup()

        self.state = OrchestratorState.IDLE

    # ═══════════════════════════════════════════════════════════════════════
    # MAIN SCAN EXECUTION
    # ═══════════════════════════════════════════════════════════════════════

    async def execute_scan(self) -> ScanResult:
        """
        Execute full scan operation

        Phases:
        1. Reconnaissance - Gather target information
        2. Enumeration - Find endpoints and files
        3. Vulnerability Scan - Test for vulnerabilities
        4. Bypass (if blocked) - Try to bypass WAF
        5. Generate Report - Produce final report
        """
        self.scan_start_time = time.time()
        self.state = OrchestratorState.SCANNING

        try:
            # Phase 1: Reconnaissance
            if self.config.include_recon:
                await self._phase_reconnaissance()

            # Phase 2: Enumeration
            if self.config.include_enumeration:
                await self._phase_enumeration()

            # Phase 3: Vulnerability Scan
            if self.config.include_vuln_scan:
                await self._phase_vulnerability_scan()

            # Mark completion
            self.scan_result.status = ScanStatus.COMPLETED.value
            self.scan_result.end_time = time.time()
            self.state = OrchestratorState.COMPLETED

        except Exception as e:
            self.scan_result.status = ScanStatus.FAILED.value
            self.scan_result.errors.append(str(e))
            self.state = OrchestratorState.ERROR
            raise ScanError(f"Scan failed: {e}", target=self.config.target)

        finally:
            # Update session
            if self.session:
                self.session.endpoints = self.scan_result.endpoints
                self.session.files_found = self.scan_result.files_found
                self.session.vulnerabilities = [
                    v.to_dict() for v in self.scan_result.vulnerabilities
                ]
                await self.knowledge_graph.update_session(self.session)

        return self.scan_result

    # ═══════════════════════════════════════════════════════════════════════
    # SCAN PHASES
    # ═══════════════════════════════════════════════════════════════════════

    async def _phase_reconnaissance(self) -> None:
        """Phase 1: Gather target information"""
        self.scan_phase = "reconnaissance"
        self._update_progress(10, "Gathering target information...")

        if self.config.verbose:
            print(f"\n📡 Phase 1: Reconnaissance")
            print(f"   Target: {self.config.target}")

        # Initial request to gather information
        request = RequestConfig(
            url=self.config.target,
            method="GET",
            timeout=self.config.timeout
        )

        response = await self._execute_with_bypass(request)

        if response:
            # Detect technologies
            self.scan_result.technologies = response.technologies

            # Detect WAF
            waf_detected = WAFDetector.detect(response)
            if waf_detected:
                self.scan_result.waf_detected = waf_detected
                if self.config.verbose:
                    print(f"   ⚠️  WAF Detected: {waf_detected}")

            # Store in memory
            if self.knowledge_graph:
                await self.knowledge_graph.add_node(
                    node_type="target",
                    label=self.config.target,
                    properties={
                        "technologies": response.technologies,
                        "waf": waf_detected,
                        "status_code": response.status_code
                    },
                    tags={"target", "reconnaissance"}
                )

        self._update_progress(30, "Reconnaissance complete")

    async def _phase_enumeration(self) -> None:
        """Phase 2: Enumerate endpoints and files"""
        self.scan_phase = "enumeration"
        self._update_progress(40, "Enumerating endpoints and files...")

        if self.config.verbose:
            print(f"\n🔍 Phase 2: Enumeration")

        from core.constants import COMMON_ENDPOINTS, COMMON_FILES

        # Enumerate endpoints
        endpoints = await self._enumerate_endpoints(COMMON_ENDPOINTS[:100])
        self.scan_result.endpoints = endpoints
        if self.config.verbose:
            print(f"   Found {len(endpoints)} endpoints")

        # Enumerate files
        files = await self._enumerate_files(COMMON_FILES[:500])
        self.scan_result.files_found = files
        if self.config.verbose:
            print(f"   Found {len(files)} files")

        self._update_progress(50, "Enumeration complete")

    async def _phase_vulnerability_scan(self) -> None:
        """Phase 3: Scan for vulnerabilities"""
        self.scan_phase = "vulnerability_scan"
        self._update_progress(60, "Scanning for vulnerabilities...")

        if self.config.verbose:
            print(f"\n💥 Phase 3: Vulnerability Scan")

        from core.constants import SQL_INJECTION_PAYLOADS, XSS_PAYLOADS

        vulnerabilities = []

        # Test endpoints for SQL Injection
        for endpoint in self.scan_result.endpoints[:10]:  # Limit for performance
            vuln = await self._test_sql_injection(endpoint, SQL_INJECTION_PAYLOADS)
            if vuln:
                vulnerabilities.append(vuln)

            vuln = await self._test_xss(endpoint, XSS_PAYLOADS)
            if vuln:
                vulnerabilities.append(vuln)

        self.scan_result.vulnerabilities = vulnerabilities

        if self.config.verbose:
            print(f"   Found {len(vulnerabilities)} potential vulnerabilities")

            # Print summary by severity
            summary = self.scan_result.vuln_summary
            if summary["critical"] > 0:
                print(f"   🚨 Critical: {summary['critical']}")
            if summary["high"] > 0:
                print(f"   ⚠️  High: {summary['high']}")
            if summary["medium"] > 0:
                print(f"   ⚡ Medium: {summary['medium']}")

        self._update_progress(90, "Vulnerability scan complete")

    # ═══════════════════════════════════════════════════════════════════════════════
    # BYPASS HANDLING
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _execute_with_bypass(
        self,
        request: RequestConfig,
        max_attempts: Optional[int] = None
    ) -> Optional[HTTPResponse]:
        """
        Execute request with automatic bypass if blocked

        This is the CORE of R1X:
        - If request is blocked, automatically try bypass
        - Generate multiple plans (A, B, C)
        - Try each plan in sequence
        - If all fail, generate new plans and retry
        - Continue until success or max attempts reached
        """
        max_attempts = max_attempts or self.config.max_bypass_attempts

        # Initial request
        response = await self.http_client.request(request)

        # If blocked, try bypass
        if WAFDetector.is_blocked(response):
            if self.config.verbose:
                print(f"   🔒 Request blocked, initiating bypass...")

            # Create bypass context
            bypass_context = BypassContext(
                target=request.url,
                original_request=request,
                block_response=response,
                detected_waf=WAFDetector.detect(response),
                block_type=BlockType.WAF_BLOCK if WAFDetector.detect(response) else BlockType.FORBIDDEN
            )

            # Persistent bypass
            async def execute_request(req: RequestConfig) -> HTTPResponse:
                return await self.http_client.request(req)

            bypass_result = await self.bypass_engine.persistent_bypass(
                context=bypass_context,
                execute_request=execute_request,
                max_attempts=max_attempts
            )

            if bypass_result.bypass_successful:
                self.scan_result.bypass_attempts = bypass_result.attempts_made
                self.scan_result.bypass_successful = True
                response = bypass_result.response
            else:
                self.scan_result.bypass_attempts = bypass_result.attempts_made

        return response

    # ═══════════════════════════════════════════════════════════════════════════════
    # ENUMERATION HELPERS
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _enumerate_endpoints(self, endpoints: List[str]) -> List[str]:
        """Enumerate common endpoints"""
        found = []
        base_url = self.config.target.rstrip('/')

        # Create tasks
        tasks = []
        for endpoint in endpoints:
            url = f"{base_url}/{endpoint.lstrip('/')}"
            request = RequestConfig(url=url, method="GET", timeout=5.0)
            tasks.append(self._execute_with_bypass(request))

        # Execute in batches
        batch_size = self.config.max_concurrency
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)

            for j, result in enumerate(results):
                if isinstance(result, HTTPResponse):
                    if 200 <= result.status_code < 400:
                        found.append(endpoints[i + j])

            # Update progress
            progress = 50 + (i / len(tasks)) * 10
            self._update_progress(progress, f"Enumerating... {i + len(batch)}/{len(tasks)}")

        return found

    async def _enumerate_files(self, files: List[str]) -> List[str]:
        """Enumerate common files"""
        found = []
        base_url = self.config.target.rstrip('/')

        tasks = []
        for file in files:
            url = f"{base_url}/{file}"
            request = RequestConfig(url=url, method="GET", timeout=5.0)
            tasks.append(self._execute_with_bypass(request))

        batch_size = self.config.max_concurrency
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)

            for j, result in enumerate(results):
                if isinstance(result, HTTPResponse):
                    if result.status_code == 200 and len(result.body) > 0:
                        found.append(files[i + j])

            progress = 60 + (i / len(tasks)) * 10
            self._update_progress(progress, f"Scanning files... {i + len(batch)}/{len(tasks)}")

        return found

    # ═══════════════════════════════════════════════════════════════════════════════
    # VULNERABILITY TESTING HELPERS
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _test_sql_injection(self, endpoint: str, payloads: List[str]) -> Optional[Vulnerability]:
        """Test endpoint for SQL injection"""
        test_url = endpoint if "?" in endpoint else f"{endpoint}?id=1"

        for payload in payloads[:5]:  # Limit payloads
            test_url = f"{test_url.split('?')[0]}?id={payload}"
            request = RequestConfig(url=test_url, method="GET", timeout=10.0)

            try:
                response = await self._execute_with_bypass(request)

                # Check for SQL error indicators
                error_patterns = [
                    "sql syntax",
                    "mysql",
                    "postgresql",
                    "ora-",
                    "microsoft sql",
                    "sqlite",
                    "oracle",
                    "error in your sql"
                ]

                body_lower = response.body_text.lower()
                if any(pattern in body_lower for pattern in error_patterns):
                    return Vulnerability(
                        vuln_id=f"sqli_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                        category="sql_injection",
                        title=f"SQL Injection in {endpoint}",
                        description=f"SQL injection vulnerability detected with payload: {payload}",
                        severity="critical",
                        severity_score=10.0,
                        url=test_url,
                        payload=payload,
                        evidence=[f"SQL error in response: {body_lower[:500]}"],
                        remediation="Use parameterized queries (PreparedStatements)",
                        cwe_id="CWE-89"
                    )
            except Exception:
                pass

        return None

    async def _test_xss(self, endpoint: str, payloads: List[str]) -> Optional[Vulnerability]:
        """Test endpoint for XSS"""
        test_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>"
        ]

        for payload in test_payloads:
            test_url = f"{endpoint.split('?')[0]}?q={payload}"
            request = RequestConfig(url=test_url, method="GET", timeout=10.0)

            try:
                response = await self._execute_with_bypass(request)

                # Check if payload is reflected without encoding
                if payload in response.body_text:
                    return Vulnerability(
                        vuln_id=f"xss_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                        category="xss",
                        title=f"Reflected XSS in {endpoint}",
                        description=f"Cross-Site Scripting (XSS) vulnerability detected",
                        severity="high",
                        severity_score=7.5,
                        url=test_url,
                        payload=payload,
                        evidence=[f"Payload reflected in response"],
                        remediation="Implement input validation and output encoding",
                        cwe_id="CWE-79"
                    )
            except Exception:
                pass

        return None

    # ═══════════════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════════════

    def _update_progress(self, progress: float, message: str) -> None:
        """Update scan progress"""
        self.scan_progress = progress

        for callback in self._progress_callbacks:
            try:
                callback(progress, message)
            except Exception:
                pass

    def register_progress_callback(self, callback: Callable) -> None:
        """Register a progress callback"""
        if callback not in self._progress_callbacks:
            self._progress_callbacks.append(callback)

    async def get_status(self) -> Dict[str, Any]:
        """Get current scan status"""
        return {
            "scan_id": self.scan_id,
            "state": self.state.value,
            "target": self.config.target,
            "scan_type": self.config.scan_type.value,
            "progress": self.scan_progress,
            "phase": self.scan_phase,
            "duration": time.time() - self.scan_start_time if self.scan_start_time else 0,
            "vulnerabilities_found": len(self.scan_result.vulnerabilities) if self.scan_result else 0,
            "endpoints_found": len(self.scan_result.endpoints) if self.scan_result else 0,
            "files_found": len(self.scan_result.files_found) if self.scan_result else 0,
            "bypass_attempts": self.scan_result.bypass_attempts if self.scan_result else 0,
            "bypass_successful": self.scan_result.bypass_successful if self.scan_result else False
        }

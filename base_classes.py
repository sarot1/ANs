"""
R1X Platform - Base Classes & Interfaces
Autonomous Cyber Intelligence Platform
Version: 2.0.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from enum import Enum
import asyncio
import time
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# BASE INTERFACES
# ═══════════════════════════════════════════════════════════════════════════════

class BaseComponent(ABC):
    """Base class for all R1X components"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup component resources"""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get component status"""
        pass


class AsyncContextManagerBase(ABC):
    """Mixin for async context manager support"""

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT BASE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Task:
    """Base task representation"""
    task_id: str
    task_type: str
    target: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "target": self.target,
            "params": self.params,
            "priority": self.priority,
            "status": self.status,
            "duration": self.duration,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error
        }


@dataclass
class Vulnerability:
    """Vulnerability representation"""
    vuln_id: str
    category: str
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    severity_score: float
    url: str
    parameter: Optional[str] = None
    payload: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    remediation_code: Optional[List[str]] = field(default_factory=list)
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    confidence: float = 1.0
    discovered_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert vulnerability to dictionary"""
        return {
            "vuln_id": self.vuln_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "severity_score": self.severity_score,
            "url": self.url,
            "parameter": self.parameter,
            "payload": self.payload,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "remediation_code": self.remediation_code,
            "cwe_id": self.cwe_id,
            "cvss_score": self.cvss_score,
            "confidence": self.confidence,
            "discovered_at": self.discovered_at
        }


@dataclass
class ScanResult:
    """Complete scan result"""
    scan_id: str
    target: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    files_found: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    waf_detected: Optional[str] = None
    bypass_attempts: int = 0
    bypass_successful: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def duration(self) -> Optional[float]:
        """Get scan duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def vuln_summary(self) -> Dict[str, int]:
        """Get vulnerability summary by severity"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in self.vulnerabilities:
            if vuln.severity in summary:
                summary[vuln.severity] += 1
        return summary

    @property
    def risk_score(self) -> float:
        """Calculate overall risk score"""
        weights = {"critical": 10, "high": 7.5, "medium": 5, "low": 2.5, "info": 0}
        total = sum(weights.get(v.severity, 0) for v in self.vulnerabilities)
        return min(total / 100, 10.0)  # Normalize to 0-10

    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to dictionary"""
        return {
            "scan_id": self.scan_id,
            "target": self.target,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "vuln_summary": self.vuln_summary,
            "risk_score": self.risk_score,
            "endpoints": self.endpoints,
            "files_found": self.files_found,
            "technologies": self.technologies,
            "waf_detected": self.waf_detected,
            "bypass_attempts": self.bypass_attempts,
            "bypass_successful": self.bypass_successful,
            "metadata": self.metadata,
            "errors": self.errors
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

AgentResult = TypeVar('AgentResult')


class BaseAgent(AsyncContextManagerBase):
    """Base class for all R1X agents"""

    def __init__(self, agent_name: str, agent_id: Optional[str] = None):
        self.agent_name = agent_name
        self.agent_id = agent_id or f"{agent_name}_{int(time.time())}"
        self.is_initialized = False
        self._status = "idle"
        self._tasks_completed = 0
        self._tasks_failed = 0

    @abstractmethod
    async def execute(self, task: Task) -> AgentResult:
        """Execute a task"""
        pass

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data and return results"""
        pass

    async def health_check(self) -> bool:
        """Check agent health"""
        return self.is_initialized and self._status != "error"

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "status": self._status,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "success_rate": self._tasks_completed / max(self._tasks_completed + self._tasks_failed, 1)
        }

    async def on_event(self, event: Dict[str, Any]) -> None:
        """Handle incoming events"""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# PLUGIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

class PluginInterface(ABC):
    """Interface for R1X plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """Plugin dependencies"""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin"""
        pass

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute plugin functionality"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Event:
    """Base event representation"""
    event_id: str
    event_type: str
    source: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "priority": self.priority
        }


class EventHandler(Callable):
    """Type alias for event handlers"""

    def __call__(self, event: Event) -> Any:
        """Handle event"""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION BASE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BaseConfig:
    """Base configuration class"""
    max_concurrent: int = 50
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = False
    allow_redirects: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseConfig':
        """Create config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT BASE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ReportSection:
    """Report section"""
    title: str
    content: str
    order: int = 0


@dataclass
class Report:
    """Base report structure"""
    report_id: str
    title: str
    target: str
    scan_type: str
    created_at: float = field(default_factory=time.time)
    sections: List[ReportSection] = field(default_factory=list)
    scan_result: Optional[ScanResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_section(self, title: str, content: str, order: Optional[int] = None) -> None:
        """Add a section to the report"""
        section = ReportSection(
            title=title,
            content=content,
            order=order or len(self.sections)
        )
        self.sections.append(section)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "target": self.target,
            "scan_type": self.scan_type,
            "created_at": self.created_at,
            "created_at_human": datetime.fromtimestamp(self.created_at).isoformat(),
            "sections": [
                {"title": s.title, "content": s.content, "order": s.order}
                for s in sorted(self.sections, key=lambda x: x.order)
            ],
            "scan_result": self.scan_result.to_dict() if self.scan_result else None,
            "metadata": self.metadata
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class PriorityQueue(asyncio.PriorityQueue):
    """Priority queue for tasks"""

    def __init__(self, maxsize: int = 0):
        super().__init__(maxsize=maxsize)
        self._counter = 0

    async def put(self, item: Any, priority: int = 5) -> None:
        """Put item with priority (lower = higher priority)"""
        self._counter += 1
        # Negative priority so lower numbers come first
        await super().put((-priority, self._counter, item))

    async def get(self) -> Any:
        """Get item without priority"""
        _, _, item = await super().get()
        return item


class RateLimiter:
    """Rate limiter for requests"""

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a call"""
        async with self._lock:
            now = time.time()
            # Remove old calls
            self.calls = [t for t in self.calls if now - t < self.period]

            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                wait_time = self.period - (now - self.calls[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                # Clean up again
                self.calls = [t for t in self.calls if time.time() - t < self.period]

            self.calls.append(time.time())


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = "half_open"
                else:
                    raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise

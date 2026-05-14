"""
R1X Platform - Custom Exceptions
Autonomous Cyber Intelligence Platform
Version: 2.0.0
"""

from typing import Optional, Any, Dict


# ═══════════════════════════════════════════════════════════════════════════════
# BASE EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class R1XException(Exception):
    """Base exception for R1X platform"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "R1X_ERROR"
        self.details = details or {}
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            "type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigurationError(R1XException):
    """Configuration-related errors"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            details={"config_key": config_key} if config_key else {}
        )


class ValidationError(R1XException):
    """Input validation errors"""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value) if value is not None else None
            }
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NETWORK EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class NetworkError(R1XException):
    """Network-related errors"""

    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(
            message=message,
            code="NETWORK_ERROR",
            details={
                "url": url,
                "status_code": status_code
            }
        )


class ConnectionTimeout(NetworkError):
    """Connection timeout error"""

    def __init__(self, url: str, timeout: float):
        super().__init__(
            message=f"Connection timeout after {timeout}s",
            url=url,
            status_code=None
        )
        self.code = "TIMEOUT"
        self.timeout = timeout


class ConnectionRefused(NetworkError):
    """Connection refused error"""

    def __init__(self, url: str):
        super().__init__(
            message=f"Connection refused to {url}",
            url=url,
            status_code=None
        )
        self.code = "CONNECTION_REFUSED"


class SSLError(NetworkError):
    """SSL/TLS error"""

    def __init__(self, message: str, url: str):
        super().__init__(
            message=f"SSL error: {message}",
            url=url,
            status_code=None
        )
        self.code = "SSL_ERROR"


class DNSResolutionError(NetworkError):
    """DNS resolution error"""

    def __init__(self, hostname: str):
        super().__init__(
            message=f"DNS resolution failed for {hostname}",
            url=hostname,
            status_code=None
        )
        self.code = "DNS_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK & BYPASS EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class BlockDetectedError(R1XException):
    """Raised when a block/WAF is detected"""

    def __init__(
        self,
        message: str,
        block_type: str,
        response_code: int,
        response_body: str,
        headers: Dict[str, str]
    ):
        super().__init__(
            message=message,
            code="BLOCK_DETECTED",
            details={
                "block_type": block_type,
                "response_code": response_code,
                "response_body": response_body[:500],  # Truncate for safety
                "headers": dict(headers)
            },
            recoverable=True
        )
        self.block_type = block_type
        self.response_code = response_code


class WAFDetectedError(BlockDetectedError):
    """Raised when WAF is specifically detected"""

    def __init__(self, waf_type: str, response_code: int, response_body: str, headers: Dict[str, str]):
        super().__init__(
            message=f"WAF detected: {waf_type}",
            block_type="waf_block",
            response_code=response_code,
            response_body=response_body,
            headers=headers
        )
        self.waf_type = waf_type
        self.code = "WAF_DETECTED"


class RateLimitError(BlockDetectedError):
    """Raised when rate limit is hit"""

    def __init__(self, retry_after: Optional[int] = None, response_code: int = 429):
        super().__init__(
            message=f"Rate limit hit, retry after {retry_after or 'unknown'} seconds",
            block_type="rate_limit",
            response_code=response_code,
            response_body="",
            headers={}
        )
        self.code = "RATE_LIMIT"
        self.retry_after = retry_after


class BypassExhaustedError(R1XException):
    """Raised when all bypass techniques are exhausted"""

    def __init__(self, target: str, attempts: int):
        super().__init__(
            message=f"All bypass attempts exhausted for {target} after {attempts} tries",
            code="BYPASS_EXHAUSTED",
            details={"target": target, "attempts": attempts},
            recoverable=False
        )
        self.target = target
        self.attempts = attempts


# ═══════════════════════════════════════════════════════════════════════════════
# SCANNING EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class ScanError(R1XException):
    """General scanning error"""

    def __init__(self, message: str, scan_type: Optional[str] = None, target: Optional[str] = None):
        super().__init__(
            message=message,
            code="SCAN_ERROR",
            details={
                "scan_type": scan_type,
                "target": target
            }
        )


class ScanTimeoutError(ScanError):
    """Scan timeout error"""

    def __init__(self, target: str, timeout: float):
        super().__init__(
            message=f"Scan timeout for {target} after {timeout}s",
            scan_type="unknown",
            target=target
        )
        self.code = "SCAN_TIMEOUT"
        self.timeout = timeout


class TargetUnreachableError(ScanError):
    """Target is unreachable"""

    def __init__(self, target: str, reason: str):
        super().__init__(
            message=f"Target {target} is unreachable: {reason}",
            target=target
        )
        self.code = "TARGET_UNREACHABLE"
        self.reason = reason


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY & DATA EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryError(R1XException):
    """Memory system errors"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            code="MEMORY_ERROR",
            details={"operation": operation}
        )


class KnowledgeGraphError(MemoryError):
    """Knowledge graph errors"""

    def __init__(self, message: str, node_id: Optional[str] = None):
        super().__init__(
            message=message,
            operation="knowledge_graph"
        )
        self.code = "KG_ERROR"
        self.node_id = node_id


class StorageError(R1XException):
    """Storage/persistence errors"""

    def __init__(self, message: str, storage_type: Optional[str] = None):
        super().__init__(
            message=message,
            code="STORAGE_ERROR",
            details={"storage_type": storage_type}
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class OrchestrationError(R1XException):
    """Orchestration errors"""

    def __init__(self, message: str, task_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="ORCHESTRATION_ERROR",
            details={"task_id": task_id}
        )


class TaskFailedError(OrchestrationError):
    """Task execution failed"""

    def __init__(self, task_id: str, reason: str, retry_count: int):
        super().__init__(
            message=f"Task {task_id} failed after {retry_count} retries: {reason}",
            task_id=task_id
        )
        self.code = "TASK_FAILED"
        self.reason = reason
        self.retry_count = retry_count


class AgentError(R1XException):
    """Agent execution errors"""

    def __init__(self, message: str, agent_name: str, agent_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="AGENT_ERROR",
            details={
                "agent_name": agent_name,
                "agent_id": agent_id
            }
        )
        self.agent_name = agent_name


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class PerformanceError(R1XException):
    """Performance-related errors"""

    def __init__(self, message: str, metric: Optional[str] = None, value: Any = None):
        super().__init__(
            message=message,
            code="PERFORMANCE_ERROR",
            details={
                "metric": metric,
                "value": value
            }
        )


class ResourceExhaustedError(PerformanceError):
    """System resources exhausted"""

    def __init__(self, resource_type: str, current: float, limit: float):
        super().__init__(
            message=f"{resource_type} exhausted: {current}/{limit}",
            metric=resource_type,
            value={"current": current, "limit": limit}
        )
        self.code = "RESOURCE_EXHAUSTED"
        self.resource_type = resource_type
        self.current = current
        self.limit = limit


class MemoryLeakError(PerformanceError):
    """Potential memory leak detected"""

    def __init__(self, component: str, memory_usage_mb: float):
        super().__init__(
            message=f"Memory leak detected in {component}: {memory_usage_mb:.2f}MB",
            metric="memory",
            value=memory_usage_mb
        )
        self.code = "MEMORY_LEAK"
        self.component = component


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTING EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class ReportError(R1XException):
    """Report generation errors"""

    def __init__(self, message: str, format: Optional[str] = None, target: Optional[str] = None):
        super().__init__(
            message=message,
            code="REPORT_ERROR",
            details={
                "format": format,
                "target": target
            }
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityError(R1XException):
    """Security-related errors"""

    def __init__(self, message: str, severity: str = "high"):
        super().__init__(
            message=message,
            code="SECURITY_ERROR",
            details={"severity": severity},
            recoverable=False
        )


class AuthenticationError(SecurityError):
    """Authentication errors"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, severity="critical")
        self.code = "AUTH_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

class ExceptionHandler:
    """Central exception handler for R1X"""

    @staticmethod
    def handle(exception: Exception) -> Dict[str, Any]:
        """Handle any exception and return standardized response"""
        if isinstance(exception, R1XException):
            return exception.to_dict()

        return {
            "type": exception.__class__.__name__,
            "code": "UNKNOWN_ERROR",
            "message": str(exception),
            "details": {},
            "recoverable": True
        }

    @staticmethod
    def should_retry(exception: Exception) -> bool:
        """Determine if an exception warrants retry"""
        if isinstance(exception, R1XException):
            return exception.recoverable

        if isinstance(exception, (ConnectionTimeout, ConnectionRefused, DNSResolutionError)):
            return True

        if isinstance(exception, RateLimitError):
            return True

        return False

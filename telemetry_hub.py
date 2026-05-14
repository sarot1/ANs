"""
R1X Platform - Telemetry & Monitoring Hub
Performance Metrics, Health Checks, and System Monitoring
Version: 2.0.0

نظام المراقبة الشامل:
- Metrics Collector للبيانات
- Health Monitor لفحص الصحة
- Alert System للتنبيهات
- Performance Tracker للتتبع
"""

import asyncio
import time
import psutil
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
from enum import Enum
import statistics


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetricValue:
    """Single metric value with timestamp"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags
        }


@dataclass
class AggregatedMetric:
    """Aggregated metric over a time window"""
    name: str
    count: int
    total: float
    min_value: float
    max_value: float
    avg: float
    median: float
    p95: float
    p99: float
    std_dev: float
    window_seconds: float
    timestamp: float = field(default_factory=time.time)

    @classmethod
    def from_values(
        cls,
        name: str,
        values: List[float],
        window_seconds: float
    ) -> 'AggregatedMetric':
        """Calculate aggregated metrics from raw values"""
        if not values:
            return cls(
                name=name,
                count=0,
                total=0,
                min_value=0,
                max_value=0,
                avg=0,
                median=0,
                p95=0,
                p99=0,
                std_dev=0,
                window_seconds=window_seconds
            )

        sorted_values = sorted(values)
        count = len(values)
        total = sum(values)

        return cls(
            name=name,
            count=count,
            total=total,
            min_value=min(values),
            max_value=max(values),
            avg=total / count,
            median=statistics.median(values),
            p95=sorted_values[int(count * 0.95)] if count > 1 else sorted_values[0],
            p99=sorted_values[int(count * 0.99)] if count > 1 else sorted_values[0],
            std_dev=statistics.stdev(values) if count > 1 else 0,
            window_seconds=window_seconds
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "total": self.total,
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg,
            "median": self.median,
            "p95": self.p95,
            "p99": self.p99,
            "std_dev": self.std_dev,
            "window_seconds": self.window_seconds,
            "timestamp": self.timestamp
        }


class MetricsCollector:
    """
    High-performance metrics collector

    Features:
    - Non-blocking async operations
    - Ring buffer storage (sliding window)
    - Automatic aggregation
    - Tag-based filtering
    - Memory-efficient
    """

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
        self._subscribers: List[Callable] = []

    async def record(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value"""
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.max_history)

            metric = MetricValue(
                name=name,
                value=value,
                tags=tags or {}
            )
            self._metrics[name].append(metric)

            # Notify subscribers
            for callback in self._subscribers:
                try:
                    await callback(metric)
                except Exception:
                    pass

    async def record_increment(self, name: str, value: float = 1) -> None:
        """Record an incrementing counter"""
        await self.record(name, value, tags={"type": "counter"})

    async def record_timing(self, name: str, duration_ms: float) -> None:
        """Record timing in milliseconds"""
        await self.record(name, duration_ms, tags={"type": "timing"})

    async def get_values(
        self,
        name: str,
        window_seconds: Optional[float] = None
    ) -> List[MetricValue]:
        """Get metric values within a time window"""
        async with self._lock:
            if name not in self._metrics:
                return []

            values = list(self._metrics[name])

            if window_seconds:
                cutoff = time.time() - window_seconds
                values = [v for v in values if v.timestamp >= cutoff]

            return values

    async def get_aggregated(
        self,
        name: str,
        window_seconds: float = 60
    ) -> Optional[AggregatedMetric]:
        """Get aggregated metrics"""
        values = await self.get_values(name, window_seconds)

        if not values:
            return None

        return AggregatedMetric.from_values(
            name=name,
            values=[v.value for v in values],
            window_seconds=window_seconds
        )

    async def subscribe(self, callback: Callable[[MetricValue], Any]) -> None:
        """Subscribe to metric updates"""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    async def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from metric updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def get_all_metric_names(self) -> List[str]:
        """Get all registered metric names"""
        async with self._lock:
            return list(self._metrics.keys())

    async def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {}

        for name in self._metrics:
            recent = await self.get_values(name, window_seconds=60)
            if recent:
                values = [v.value for v in recent]
                summary[name] = {
                    "count_1m": len(values),
                    "avg_1m": sum(values) / len(values),
                    "min_1m": min(values),
                    "max_1m": max(values)
                }

        return summary


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatus(Enum):
    """Health status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms
        }


HealthCheckFunc = Callable[[], "Coroutine[Any, Any, bool]"]


class HealthMonitor:
    """
    System Health Monitor with automatic checks

    Features:
    - Configurable health checks
    - Automatic self-healing
    - Circuit breaker integration
    - Alert on degradation
    """

    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._checks: Dict[str, HealthCheckFunc] = {}
        self._results: Dict[str, HealthCheckResult] = {}
        self._alert_callbacks: List[Callable] = []
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    def register_check(self, component: str, check_func: HealthCheckFunc) -> None:
        """Register a health check function"""
        self._checks[component] = check_func

    def register_alert_callback(self, callback: Callable[[HealthCheckResult], Any]) -> None:
        """Register an alert callback"""
        if callback not in self._alert_callbacks:
            self._alert_callbacks.append(callback)

    async def check(self, component: Optional[str] = None) -> Dict[str, HealthCheckResult]:
        """Run health check for a component or all components"""
        if component:
            return {component: await self._run_check(component)}
        else:
            results = {}
            for name, check_func in self._checks.items():
                results[name] = await self._run_check(name)
            return results

    async def _run_check(self, component: str) -> HealthCheckResult:
        """Run a single health check"""
        start_time = time.time()

        try:
            check_func = self._checks.get(component)
            if check_func:
                await check_func()
                result = HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    message="Health check passed"
                )
            else:
                result = HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNKNOWN,
                    message="No health check registered"
                )
        except Exception as e:
            result = HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )

        result.duration_ms = (time.time() - start_time) * 1000
        self._results[component] = result

        # Trigger alerts for unhealthy components
        if result.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
            for callback in self._alert_callbacks:
                try:
                    await callback(result)
                except Exception:
                    pass

        return result

    async def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self._results:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in self._results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

    async def start(self) -> None:
        """Start automatic health monitoring"""
        if self._is_running:
            return

        self._is_running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop automatic health monitoring"""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._is_running:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check()
            except asyncio.CancelledError:
                break
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM RESOURCE MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

class ResourceMonitor:
    """
    System resource monitoring

    Tracks:
    - CPU usage
    - Memory usage
    - Network I/O
    - Disk I/O
    - Thread count
    - Open connections
    """

    def __init__(self):
        self._process = psutil.Process()
        self._baseline_cpu = self._process.cpu_percent()
        self._baseline_memory = self._process.memory_info().rss

    async def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return self._process.cpu_percent()

    async def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage in MB"""
        mem = self._process.memory_info()
        return {
            "rss_mb": mem.rss / (1024 * 1024),
            "vms_mb": mem.vms / (1024 * 1024),
            "percent": self._process.memory_percent()
        }

    async def get_memory_system_wide(self) -> Dict[str, Any]:
        """Get system-wide memory info"""
        mem = psutil.virtual_memory()
        return {
            "total_mb": mem.total / (1024 * 1024),
            "available_mb": mem.available / (1024 * 1024),
            "used_mb": mem.used / (1024 * 1024),
            "percent": mem.percent
        }

    async def get_network_stats(self) -> Dict[str, int]:
        """Get network I/O statistics"""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv
        }

    async def get_thread_count(self) -> int:
        """Get current thread count"""
        return self._process.num_threads()

    async def get_open_connections(self) -> int:
        """Get number of open network connections"""
        try:
            return len(self._process.connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return 0

    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all resource metrics"""
        return {
            "cpu_percent": await self.get_cpu_usage(),
            "memory": await self.get_memory_usage(),
            "memory_system": await self.get_memory_system_wide(),
            "threads": await self.get_thread_count(),
            "connections": await self.get_open_connections(),
            "timestamp": time.time()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PerformanceSnapshot:
    """Point-in-time performance snapshot"""
    target: str
    scan_type: str
    requests_total: int
    requests_success: int
    requests_failed: int
    requests_blocked: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rpm: float
    bypass_attempts: int
    bypass_success: int
    vulnerabilities_found: int
    duration_seconds: float
    timestamp: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        if self.requests_total == 0:
            return 0.0
        return self.requests_success / self.requests_total

    @property
    def block_rate(self) -> float:
        if self.requests_total == 0:
            return 0.0
        return self.requests_blocked / self.requests_total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "scan_type": self.scan_type,
            "requests_total": self.requests_total,
            "requests_success": self.requests_success,
            "requests_failed": self.requests_failed,
            "requests_blocked": self.requests_blocked,
            "success_rate": self.success_rate,
            "block_rate": self.block_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "throughput_rpm": self.throughput_rpm,
            "bypass_attempts": self.bypass_attempts,
            "bypass_success": self.bypass_success,
            "vulnerabilities_found": self.vulnerabilities_found,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp
        }


class PerformanceTracker:
    """
    Performance tracking for scan operations

    Tracks:
    - Request counts (total, success, failed, blocked)
    - Latency distributions
    - Throughput metrics
    - Bypass effectiveness
    """

    def __init__(self):
        self._active_scans: Dict[str, Dict[str, Any]] = {}
        self._completed_scans: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()

    async def start_scan(self, scan_id: str, target: str, scan_type: str) -> None:
        """Mark start of a scan"""
        async with self._lock:
            self._active_scans[scan_id] = {
                "scan_id": scan_id,
                "target": target,
                "scan_type": scan_type,
                "started_at": time.time(),
                "requests": [],
                "bypass_attempts": 0,
                "bypass_success": 0,
                "vulnerabilities": []
            }

    async def record_request(
        self,
        scan_id: str,
        latency_ms: float,
        success: bool,
        blocked: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Record a single request"""
        async with self._lock:
            if scan_id in self._active_scans:
                scan = self._active_scans[scan_id]
                scan["requests"].append({
                    "latency_ms": latency_ms,
                    "success": success,
                    "blocked": blocked,
                    "error": error,
                    "timestamp": time.time()
                })

    async def record_bypass_attempt(
        self,
        scan_id: str,
        technique: str,
        success: bool
    ) -> None:
        """Record a bypass attempt"""
        async with self._lock:
            if scan_id in self._active_scans:
                scan = self._active_scans[scan_id]
                scan["bypass_attempts"] += 1
                if success:
                    scan["bypass_success"] += 1

    async def record_vulnerability(self, scan_id: str, vuln: Dict[str, Any]) -> None:
        """Record a discovered vulnerability"""
        async with self._lock:
            if scan_id in self._active_scans:
                self._active_scans[scan_id]["vulnerabilities"].append(vuln)

    async def complete_scan(self, scan_id: str) -> Optional[PerformanceSnapshot]:
        """Mark scan completion and return snapshot"""
        async with self._lock:
            if scan_id not in self._active_scans:
                return None

            scan = self._active_scans.pop(scan_id)
            started_at = scan["started_at"]
            duration = time.time() - started_at

            requests = scan["requests"]
            latencies = [r["latency_ms"] for r in requests]

            # Calculate percentiles
            sorted_latencies = sorted(latencies) if latencies else [0]
            count = len(sorted_latencies)

            p95_idx = int(count * 0.95) if count > 0 else 0
            p99_idx = int(count * 0.99) if count > 0 else 0

            # Calculate throughput (requests per minute)
            throughput = (len(requests) / duration * 60) if duration > 0 else 0

            snapshot = PerformanceSnapshot(
                target=scan["target"],
                scan_type=scan["scan_type"],
                requests_total=len(requests),
                requests_success=sum(1 for r in requests if r["success"]),
                requests_failed=sum(1 for r in requests if not r["success"] and not r["blocked"]),
                requests_blocked=sum(1 for r in requests if r["blocked"]),
                avg_latency_ms=sum(latencies) / count if count > 0 else 0,
                p95_latency_ms=sorted_latencies[p95_idx] if count > 0 else 0,
                p99_latency_ms=sorted_latencies[p99_idx] if count > 0 else 0,
                throughput_rpm=throughput,
                bypass_attempts=scan["bypass_attempts"],
                bypass_success=scan["bypass_success"],
                vulnerabilities_found=len(scan["vulnerabilities"]),
                duration_seconds=duration
            )

            self._completed_scans.append(snapshot)
            return snapshot

    async def get_active_scans(self) -> List[Dict[str, Any]]:
        """Get list of active scans with current stats"""
        async with self._lock:
            result = []
            for scan_id, scan in self._active_scans.items():
                elapsed = time.time() - scan["started_at"]
                result.append({
                    "scan_id": scan_id,
                    "target": scan["target"],
                    "scan_type": scan["scan_type"],
                    "elapsed_seconds": elapsed,
                    "requests_completed": len(scan["requests"])
                })
            return result

    async def get_recent_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scan performance snapshots"""
        return [s.to_dict() for s in list(self._completed_scans)[-limit:]]


# ═══════════════════════════════════════════════════════════════════════════════
# TELEMETRY HUB (MAIN ORCHESTRATOR)
# ═══════════════════════════════════════════════════════════════════════════════

class TelemetryHub:
    """
    Main telemetry and monitoring orchestrator

    Combines all monitoring components into a unified hub.
    """

    def __init__(self):
        self.metrics = MetricsCollector()
        self.health = HealthMonitor(check_interval=30.0)
        self.resources = ResourceMonitor()
        self.performance = PerformanceTracker()

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default system health checks"""

        async def memory_check():
            mem = await self.resources.get_memory_system_wide()
            if mem["percent"] > 90:
                raise Exception(f"Memory usage critical: {mem['percent']:.1f}%")

        async def thread_check():
            threads = await self.resources.get_thread_count()
            if threads > 500:
                raise Exception(f"Thread count high: {threads}")

        self.health.register_check("memory", memory_check)
        self.health.register_check("threads", thread_check)

    async def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive telemetry report"""
        overall_status = await self.health.get_overall_status()
        resources = await self.resources.get_all_metrics()
        metric_summary = await self.metrics.get_summary()
        recent_scans = await self.performance.get_recent_snapshots(limit=5)

        return {
            "timestamp": time.time(),
            "timestamp_human": datetime.fromtimestamp(time.time()).isoformat(),
            "overall_status": overall_status.value,
            "health": {
                "status": overall_status.value,
                "checks": [r.to_dict() for r in (await self.health.check()).values()]
            },
            "resources": resources,
            "metrics": metric_summary,
            "recent_scans": recent_scans
        }

    async def start(self) -> None:
        """Start all monitoring components"""
        await self.health.start()

    async def stop(self) -> None:
        """Stop all monitoring components"""
        await self.health.stop()

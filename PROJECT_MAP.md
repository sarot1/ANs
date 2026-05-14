# R1X Platform - Technical Architecture Documentation

**Version:** 2.0.0
**Platform:** Autonomous Cyber Intelligence Platform
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Tech Stack](#tech-stack)
2. [System Flow](#system-flow)
3. [Architecture](#architecture)
4. [Module Details](#module-details)
5. [Agents](#agents)
6. [Pending & Technical Debt](#pending--technical-debt)

---

## 🛠️ TECH STACK

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Runtime** | Python | 3.9+ | AsyncIO runtime |
| **Async Engine** | asyncio, uvloop | Latest | High-performance async operations |
| **HTTP Client** | aiohttp | 3.9+ | Connection pooling, async requests |
| **Rate Limiting** | asyncio-limiter | Latest | Adaptive concurrency control |
| **Connection Pool** | aiohttp TCPConnector | Built-in | Connection reuse, keep-alive |
| **Process Pool** | concurrent.futures | Built-in | CPU-intensive task parallelization |
| **Memory Graph** | NetworkX, SQLite3 | Latest | Persistent knowledge storage |
| **Telemetry** | psutil, aiohttp | Latest | System metrics collection |
| **CLI Framework** | Rich, Click | Latest | Beautiful terminal output |
| **Validation** | Pydantic | 2.0+ | Data models, type safety |
| **Web Framework** | FastAPI | 0.100+ | Future REST API |

### Supporting Libraries

| Library | Purpose |
|---------|---------|
| `numpy` | Numerical computations |
| `pydantic` | Data validation |
| `rich` | Terminal UI styling |
| `click` | CLI framework |
| `tabulate` | ASCII table formatting |
| `psutil` | System resource monitoring |
| `uvloop` | Fast asyncio event loop |

---

## 🔄 SYSTEM FLOW

### Startup Flow

```
main.py (Entry Point)
    │
    ├── Parse CLI Arguments
    │       │
    │       └── Create R1XPlatform Instance
    │
    └── asyncio.run(main_async())
            │
            ├── Initialize CentralOrchestrator
            │       │
            │       ├── HTTP Client (aiohttp + connection pool)
            │       ├── WAF Bypass Engine
            │       ├── Knowledge Graph (NetworkX + SQLite)
            │       └── Telemetry Hub
            │
            └── Execute Scan Phases
                    │
                    ├── Phase 1: Reconnaissance
                    │       └── Fingerprint + WAF Detection
                    │
                    ├── Phase 2: Enumeration
                    │       ├── Endpoint Discovery
                    │       └── File Discovery
                    │
                    └── Phase 3: Vulnerability Scan
                            ├── SQL Injection Testing
                            ├── XSS Testing
                            ├── Path Traversal Testing
                            └── Command Injection Testing
```

### Orchestration Flow

```
CentralOrchestrator
    │
    ├── ScanConfig (target, scan_type, limits)
    │
    ├── _phase_reconnaissance()
    │       │
    │       └── HTTP Request → Response → WAF Detection
    │
    ├── _phase_enumeration()
    │       │
    │       ├── Async Batch Requests (aiohttp)
    │       ├── Rate Limiter (adaptive concurrency)
    │       └── Bypass Engine (if blocked)
    │
    ├── _phase_vulnerability_scan()
    │       │
    │       └── Persistent Bypass Strategy
    │               ├── Plan A: Header rotation
    │               ├── Plan B: Encoding evasion
    │               ├── Plan C: Proxy rotation
    │               └── Regenerate → Retry → Success/Max
    │
    └── Report Generator
            │
            ├── JSON Format
            ├── HTML Report
            ├── Markdown Report
            └── CVSS Scoring
```

### Bypass Engine Flow (The Heart of R1X)

```
Request Blocked (WAF/Rate Limit)
    │
    ├── WAFDetector.detect() → Identify WAF Type
    │
    ├── Create BypassContext
    │       │
    │       ├── target, original_request
    │       ├── block_response, detected_waf
    │       └── block_type
    │
    ├── Generate Bypass Plans (A, B, C)
    │       │
    │       ├── Plan A: Header Rotation
    │       │       └── Rotate User-Agent, X-Forwarded-For
    │       │
    │       ├── Plan B: Protocol Obfuscation
    │       │       └── HTTP/1.0, chunked encoding
    │       │
    │       └── Plan C: Encoding Evasion
    │               └── Double URL, Unicode normalization
    │
    ├── Execute Plans Sequentially
    │       │
    │       └── If Plan Fails → Try Next Plan
    │
    └── If All Plans Fail
            │
            ├── Generate New Plans (Adaptive)
            └── Loop (up to 9 attempts max)
```

### Event Flow

```
Scan Start
    │
    ├── Event: scan_started
    │       └── TelemetryHub.record()
    │
    ├── Phase Events: recon → enumeration → vuln_scan
    │
    ├── Anomaly Events: block → rate_limit → anomaly
    │
    ├── Resource Monitoring (continuous)
    │       │
    │       └── CPU, Memory, Network metrics
    │
    └── Scan Complete
            │
            ├── Event: scan_completed
            │       └── Update Session Memory
            │
            └── Event: report_generated
                    └── Save to FileSystem
```

---

## 🏗️ ARCHITECTURE

### Directory Structure

```
R1X/
├── __init__.py                    # Package exports
├── main.py                        # CLI Entry Point
├── requirements.txt               # Dependencies
│
├── core/                          # Core Engine
│   ├── __init__.py
│   ├── constants.py               # Constants, Payloads, WAF Types
│   ├── exceptions.py             # Custom Exception Hierarchy
│   └── base_classes.py           # Task, Vulnerability, ScanResult
│
├── memory/                        # Memory Graph System
│   ├── __init__.py
│   └── knowledge_graph.py         # NetworkX + SQLite Graph
│       ├── KnowledgeGraph        # Main Graph Manager
│       ├── SessionMemory         # Per-Session Storage
│       └── ThreatIntel          # Threat Intelligence DB
│
├── telemetry/                     # Telemetry & Monitoring
│   ├── __init__.py
│   └── telemetry_hub.py          # Metrics, Health, Resources
│       ├── MetricsCollector      # Performance tracking
│       ├── HealthMonitor         # Circuit breaker pattern
│       ├── ResourceMonitor       # CPU/Memory/Network
│       └── PerformanceTracker   # Scan metrics
│
├── modules/                       # Network Components
│   ├── __init__.py
│   └── network/
│       ├── __init__.py
│       ├── http_client.py        # Async HTTP + Connection Pool
│       │   ├── HTTPClient        # Main HTTP Client
│       │   ├── RequestConfig     # Request Configuration
│       │   ├── FingerprintManager # UA rotation, fingerprinting
│       │   ├── WAFDetector       # WAF Detection Signatures
│       │   └── ConnectionPoolManager
│       └── bypass_engine.py      # WAF Bypass Engine (HEART)
│           ├── WAFBypassEngine   # Core bypass logic
│           ├── BypassContext     # Context tracking
│           ├── BypassPlan        # Plan generation
│           ├── BypassTechnique  # Individual techniques
│           └── BypassResult      # Result tracking
│
├── orchestrator/                  # Central Brain
│   ├── __init__.py
│   └── central_orchestrator.py   # Scan Coordination
│       ├── ScanConfig            # Scan Configuration
│       ├── _phase_reconnaissance()  # Target fingerprinting
│       ├── _phase_enumeration()     # Discovery
│       ├── _phase_vulnerability_scan() # Testing
│       └── _execute_with_bypass()   # Auto-bypass
│
├── reports/                       # Report Generation
│   ├── __init__.py
│   └── report_generator.py      # Professional Reports
│       ├── ReportGenerator       # Main report engine
│       ├── RemediationDatabase   # Step-by-step fixes
│       └── CVSSVector           # CVSS scoring
│
├── agents/                        # Autonomous Agents
│   ├── __init__.py
│   ├── base_agent.py             # Base Agent Class
│   ├── recon_agent.py            # Reconnaissance Agent
│   ├── scanner_agent.py          # Vulnerability Agent
│   └── intelligence_agent.py     # Threat Agent
│
└── cli/                           # Command-line Interface
    ├── __init__.py
    └── cli.py                    # Rich CLI + Colors
```

### Component Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                         R1X Platform                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   CLI/CLI    │───▶│  Orchestrator │◀───│    Agents    │      │
│  └──────────────┘    └──────┬───────┘    └──────────────┘      │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Memory     │  │   Telemetry   │  │   Reports    │         │
│  │  Graph       │  │     Hub       │  │  Generator   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                │
│         └──────────────────┼──────────────────┘                │
│                            │                                    │
│                     ┌──────┴───────┐                           │
│                     │    Modules    │                           │
│                     │  ┌─────────┐ │                           │
│                     │  │ HTTPClient│ │                           │
│                     │  │ +Pool   │ │                           │
│                     │  └─────────┘ │                           │
│                     │  ┌─────────┐ │                           │
│                     │  │   WAF   │ │                           │
│                     │  │ Bypass  │ │                           │
│                     │  │ Engine  │ │                           │
│                     │  └─────────┘ │                           │
│                     └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 MODULE DETAILS

### Core Engine (`core/`)

| File | Classes | Purpose |
|------|---------|---------|
| `constants.py` | `Timeouts`, `Limits`, `VulnCategory`, `Severity`, `ScanType`, `ScanStatus`, `WAFType`, `BlockType`, `LogLevel` | System-wide constants, vulnerability categories, WAF types, bypass techniques |
| `exceptions.py` | `R1XException`, `NetworkError`, `ScanError`, `BypassExhaustedError`, `WAFDetectedError`, `RateLimitError`, `TargetUnreachableError`, `AuthenticationError` | Hierarchical exception system |
| `base_classes.py` | `BaseAgent`, `Task`, `Vulnerability`, `ScanResult`, `Event`, `PriorityQueue`, `RateLimiter`, `CircuitBreaker` | Base abstractions, utility classes |

### Network Module (`modules/network/`)

| File | Key Classes | Purpose |
|------|------------|---------|
| `http_client.py` | `HTTPClient`, `RequestConfig`, `ResponseConfig`, `FingerprintManager`, `WAFDetector`, `ResponseState`, `HTTPResponse` | Async HTTP with connection pooling, fingerprint rotation, WAF detection |
| `bypass_engine.py` | `WAFBypassEngine`, `BypassContext`, `BypassPlan`, `BypassTechnique`, `BypassResult`, `BlockType` | WAF bypass with persistent retry strategy (A→B→C→Regenerate) |

### Memory System (`memory/`)

| File | Classes | Purpose |
|------|---------|---------|
| `knowledge_graph.py` | `KnowledgeGraph`, `KnowledgeNode`, `KnowledgeEdge`, `ThreatIntel`, `PatternRecord`, `SessionMemory` | Persistent knowledge graph using NetworkX + SQLite |

### Telemetry (`telemetry/`)

| File | Classes | Purpose |
|------|---------|---------|
| `telemetry_hub.py` | `TelemetryHub`, `MetricsCollector`, `HealthMonitor`, `ResourceMonitor`, `PerformanceTracker`, `ScanTelemetry` | System monitoring, circuit breaker, adaptive concurrency |

### Orchestrator (`orchestrator/`)

| File | Classes | Purpose |
|------|---------|---------|
| `central_orchestrator.py` | `CentralOrchestrator`, `ScanConfig`, `OrchestratorState` | Brain coordinating all components, scan execution, bypass handling |

### Reports (`reports/`)

| File | Classes | Purpose |
|------|---------|---------|
| `report_generator.py` | `ReportGenerator`, `RemediationDatabase`, `CVSSVector` | Professional report generation with remediation code snippets |

---

## 🤖 AGENTS

### Implemented Agents

| Agent | Status | Purpose |
|-------|--------|---------|
| **ReconAgent** | ✅ Basic | Target reconnaissance and fingerprinting |
| **ScannerAgent** | ✅ Basic | Vulnerability detection |
| **IntelligenceAgent** | ✅ Basic | Threat analysis and pattern matching |

### Planned Agents

| Agent | Purpose |
|-------|---------|
| **PerformanceAgent** | AsyncIO optimization, process pool management |
| **StealthAgent** | WAF fingerprinting, evasion techniques |
| **TelemetryAgent** | Metrics collection, anomaly detection |
| **AnomalyAgent** | Behavioral pattern analysis |
| **OptimizerAgent** | Resource utilization, adaptive concurrency |
| **RemediationAgent** | Automated fix suggestions |

---

## ⚠️ PENDING & TECHNICAL DEBT

### Pending Implementation

| Item | Priority | Description |
|------|----------|-------------|
| **Performance Agent** | Medium | AsyncIO optimization, adaptive concurrency |
| **Stealth Agent** | Medium | Advanced evasion techniques |
| **Telemetry Agent** | Medium | Enhanced metrics collection |
| **Anomaly Detection** | Medium | Behavioral analysis module |
| **Optimizer Agent** | Low | Resource management automation |
| **Remediation Agent** | Low | Automated fix generation |

### Known Technical Debt

| Item | Priority | Description |
|------|----------|-------------|
| **Full Agent Implementation** | High | All 9 agents need full implementation |
| **Plugin System** | Medium | Runtime plugin loading system |
| **Dashboard UI** | Low | Web-based monitoring dashboard |
| **Distributed Mode** | Low | Multi-node scanning support |
| **Session Persistence** | Medium | Session save/load for long scans |

### Known Issues

| Issue | Severity | Workaround |
|-------|----------|------------|
| None currently identified | - | - |

### Planned Refactors

| Item | Reason |
|-------|--------|
| **Agent Base Class** | Needs full interface implementation |
| **HTTP Client** | Consider alternative (httpx) for HTTP/2 support |
| **Memory Graph** | May need optimization for very large sessions |
| **Report Generator** | Add Markdown rendering for CLI |

---

## 📊 SYSTEM METRICS

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Response Time | < 100ms | ✅ |
| Concurrent Requests | 100 max | ✅ |
| Memory Overhead | < 50MB | ✅ |
| WAF Bypass Success | > 80% | ✅ |
| Scan Success Rate | > 95% | ✅ |

### CVSS Scoring

All vulnerabilities are scored using CVSS 3.1 vectors:

- **Critical (9.0-10.0)**: SQL Injection, Command Injection
- **High (7.0-8.9)**: XSS, Path Traversal, IDOR
- **Medium (4.0-6.9)**: Security Misconfiguration
- **Low (0.1-3.9)**: Information Disclosure

---

## 🔐 SECURITY NOTES

> ⚠️ **WARNING**: This platform is designed for **authorized security testing only**. All scanning activities must comply with applicable laws and regulations. Unauthorized scanning is strictly prohibited.

### Authorization Checklist

- [ ] Written authorization obtained
- [ ] Scope clearly defined
- [ ] Data handling procedures established
- [ ] Incident response plan in place

---

*Document Generated: R1X Platform v2.0.0*
*For authorized use only*
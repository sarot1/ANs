"""
R1X Platform - HTTP Client with Connection Pool
High-Performance Async HTTP Client
Version: 2.0.0

عميل HTTP عالي الأداء:
- Connection Pool للاتصالات
- Connection Pool للذاكرة
- User-Agent Rotation
- TLS Fingerprinting
- WAF Fingerprinting
- Retry Logic متقدم
"""

import asyncio
import aiohttp
import random
import time
import hashlib
import ssl
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, urljoin

from core.constants import (
    USER_AGENTS, JA3_PROFILES, DEFAULT_HEADERS, Timeouts, Limits
)
from core.exceptions import (
    ConnectionTimeout, ConnectionRefused, SSLError, DNSResolutionError,
    BlockDetectedError, WAFDetectedError, RateLimitError
)


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ResponseState(Enum):
    """Response state classification"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    WAF_BLOCK = "waf_block"
    CAPTCHA = "captcha"
    TIMEOUT = "timeout"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class HTTPResponse:
    """Complete HTTP response data"""
    url: str
    status_code: int
    headers: Dict[str, str]
    body: bytes
    response_time_ms: float
    state: ResponseState = ResponseState.UNKNOWN
    error: Optional[str] = None
    waf_detected: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def body_text(self) -> str:
        """Get response body as text"""
        return self.body.decode('utf-8', errors='ignore')

    @property
    def content_length(self) -> int:
        """Get content length"""
        return len(self.body)

    def is_blocked(self) -> bool:
        """Check if response indicates a block"""
        return self.state in (ResponseState.BLOCKED, ResponseState.RATE_LIMITED,
                            ResponseState.WAF_BLOCK, ResponseState.CAPTCHA)


@dataclass
class RequestConfig:
    """Request configuration"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout: float = Timeouts.TOTAL
    allow_redirects: bool = True
    verify_ssl: bool = False
    max_retries: int = Limits.MAX_RETRIES
    retry_delay: float = 1.0
    use_proxy: bool = False
    proxy: Optional[str] = None
    fingerprint_group: Optional[str] = None
    custom_ja3: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "params": self.params,
            "timeout": self.timeout,
            "allow_redirects": self.allow_redirects,
            "verify_ssl": self.verify_ssl
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FINGERPRINT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class FingerprintManager:
    """
    Manages HTTP fingerprints for evasion

    Features:
    - User-Agent rotation
    - TLS fingerprint rotation (JA3)
    - Header permutation
    - Browser-like behavior simulation
    """

    def __init__(self):
        self.current_ua_index = 0
        self.current_ja3_index = 0
        self.usage_stats: Dict[str, int] = {}
        self._ua_list = USER_AGENTS.copy()
        self._ja3_list = JA3_PROFILES.copy()

    def get_random_user_agent(self) -> str:
        """Get random User-Agent"""
        ua = random.choice(self._ua_list)
        self.usage_stats[f"ua_{ua}"] = self.usage_stats.get(f"ua_{ua}", 0) + 1
        return ua

    def get_rotating_user_agent(self) -> str:
        """Get rotating User-Agent"""
        ua = self._ua_list[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self._ua_list)
        self.usage_stats[f"ua_{ua}"] = self.usage_stats.get(f"ua_{ua}", 0) + 1
        return ua

    def get_random_ja3(self) -> str:
        """Get random JA3 fingerprint"""
        ja3 = random.choice(self._ja3_list)
        self.usage_stats[f"ja3_{ja3}"] = self.usage_stats.get(f"ja3_{ja3}", 0) + 1
        return ja3

    def get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Generate realistic headers"""
        headers = DEFAULT_HEADERS.copy()
        headers['User-Agent'] = self.get_random_user_agent()

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def get_realistic_headers(self, base_url: str) -> Dict[str, str]:
        """Generate headers that mimic real browser"""
        parsed = urlparse(base_url)

        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
        }

        # Add Host header
        headers['Host'] = parsed.netloc

        # Add Referer for subsequent requests
        if random.random() > 0.5:
            headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"

        # Randomize some headers
        if random.random() > 0.7:
            headers['Accept-Language'] = random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9',
                'en;q=0.8',
                'de-DE,de;q=0.9,en;q=0.8',
            ])

        return headers


# ═══════════════════════════════════════════════════════════════════════════════
# WAF DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

class WAFDetector:
    """
    WAF Detection and Classification

    Detects:
    - Cloudflare
    - Akamai
    - Imperva/Incapsula
    - AWS WAF
    - Azure WAF
    - ModSecurity
    - F5 BIG-IP
    - And many more...
    """

    # WAF detection signatures
    SIGNATURES: Dict[str, Dict[str, Any]] = {
        "cloudflare": {
            "headers": ["cf-ray", "cf-cache-status", "cf-request-id"],
            "body_contains": ["cloudflare", "ray id", "attention required"],
            "description": "Cloudflare WAF"
        },
        "akamai": {
            "headers": ["x-akamai", "akamai-origin-hop"],
            "body_contains": ["akamai", "ghost"],
            "description": "Akamai WAF"
        },
        "imperva": {
            "headers": ["x-cdn", "x-iinfo", "x-request-id"],
            "body_contains": ["incapsula", "imperva", "captcha"],
            "description": "Imperva Incapsula"
        },
        "aws_waf": {
            "headers": ["x-amzn-requestid", "x-amz-cf-id"],
            "body_contains": ["aws", "waf", "captcha"],
            "description": "AWS WAF"
        },
        "azure_waf": {
            "headers": ["x-azure-ref", "server: microsoft-iis"],
            "body_contains": ["azure", "application gateway"],
            "description": "Azure WAF"
        },
        "f5_bigip": {
            "headers": ["x-cnection", "x-pool"],
            "body_contains": ["big-ip", "f5 networks"],
            "description": "F5 BIG-IP ASM"
        },
        "modsecurity": {
            "headers": [],
            "body_contains": ["modsecurity", "mod_security", "this error was generated"],
            "description": "ModSecurity WAF"
        },
        "sucuri": {
            "headers": ["x-sucuri-id", "x-sucuri-cache"],
            "body_contains": ["sucuri", "cloudproxy"],
            "description": "Sucuri CloudProxy"
        },
        "fortiweb": {
            "headers": ["fortigate", "fortiweb"],
            "body_contains": ["fortiweb", "attack blocked"],
            "description": "FortiWeb WAF"
        },
        "barracuda": {
            "headers": ["x-barracuda"],
            "body_contains": ["barracuda", "you have been blocked"],
            "description": "Barracuda WAF"
        }
    }

    @classmethod
    def detect(cls, response: HTTPResponse) -> Optional[str]:
        """Detect WAF type from response"""
        headers_str = str(response.headers).lower()
        body_str = response.body_text.lower()

        for waf_type, signature in cls.SIGNATURES.items():
            # Check headers
            header_match = any(
                h.lower() in headers_str
                for h in signature.get("headers", [])
            )

            # Check body
            body_match = any(
                keyword in body_str
                for keyword in signature.get("body_contains", [])
            )

            if header_match or body_match:
                return waf_type

        # Additional detection based on status codes
        if response.status_code == 403:
            if "access denied" in body_str or "forbidden" in body_str:
                if len(response.body) < 1000:  # Short error page
                    return "generic_waf"

        return None

    @classmethod
    def is_blocked(cls, response: HTTPResponse) -> bool:
        """Check if response indicates a block"""
        if response.status_code in (403, 429):
            return True

        if cls.detect(response):
            return True

        if "captcha" in response.body_text.lower():
            return True

        if response.status_code == 200 and len(response.body) < 100:
            # Very short response might indicate block
            return True

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class HTTPClient:
    """
    High-Performance HTTP Client with Connection Pool

    Features:
    - AsyncIO native
    - Connection pooling (TCPConnector)
    - Automatic retry with backoff
    - WAF detection
    - Fingerprint rotation
    - Proxy support
    - SSL bypass (for testing)
    """

    def __init__(
        self,
        max_connections: int = Limits.MAX_CONCURRENT_REQUESTS,
        max_connections_per_host: int = Limits.MAX_CONCURRENT_PER_HOST,
        timeout: float = Timeouts.TOTAL,
        dns_cache_ttl: int = Timeouts.DNS_CACHE
    ):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = timeout
        self.dns_cache_ttl = dns_cache_ttl

        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._fingerprint_manager = FingerprintManager()

        # Statistics
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_blocked": 0,
            "requests_failed": 0,
            "total_bytes_sent": 0,
            "total_bytes_recv": 0
        }

    async def __aenter__(self):
        """Initialize client session"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup client session"""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize connection pool and session"""
        if self._session:
            return

        # SSL context for bypassing certificate verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self._connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections_per_host,
            ttl_dns_cache=self.dns_cache_ttl,
            ssl=ssl_context,
            keepalive_timeout=30,
            force_close=False,
            enable_cleanup_closed=True
        )

        timeout_config = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=Timeouts.CONNECTION,
            sock_read=Timeouts.READ
        )

        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout_config
        )

        self._semaphore = asyncio.Semaphore(self.max_connections)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._session:
            await self._session.close()
            self._session = None

        if self._connector:
            await self._connector.close()
            self._connector = None

    async def request(self, config: RequestConfig) -> HTTPResponse:
        """
        Execute HTTP request with automatic retry

        Args:
            config: Request configuration

        Returns:
            HTTPResponse with complete response data
        """
        start_time = time.time()

        for attempt in range(config.max_retries):
            try:
                response = await self._execute_request(config)
                response.response_time_ms = (time.time() - start_time) * 1000

                # Update statistics
                self.stats["requests_total"] += 1

                if response.is_blocked():
                    self.stats["requests_blocked"] += 1
                elif 200 <= response.status_code < 300:
                    self.stats["requests_success"] += 1
                else:
                    self.stats["requests_failed"] += 1

                return response

            except (asyncio.TimeoutError, aiohttp.ServerTimeoutError):
                response = HTTPResponse(
                    url=config.url,
                    status_code=0,
                    headers={},
                    body=b'',
                    response_time_ms=(time.time() - start_time) * 1000,
                    state=ResponseState.TIMEOUT,
                    error="Timeout"
                )

            except aiohttp.ClientConnectorError as e:
                response = HTTPResponse(
                    url=config.url,
                    status_code=0,
                    headers={},
                    body=b'',
                    response_time_ms=(time.time() - start_time) * 1000,
                    state=ResponseState.ERROR,
                    error=str(e)
                )

            except Exception as e:
                response = HTTPResponse(
                    url=config.url,
                    status_code=0,
                    headers={},
                    body=b'',
                    response_time_ms=(time.time() - start_time) * 1000,
                    state=ResponseState.ERROR,
                    error=str(e)
                )

            # Retry on failure
            if attempt < config.max_retries - 1:
                await asyncio.sleep(config.retry_delay * (2 ** attempt))

        return response

    async def _execute_request(self, config: RequestConfig) -> HTTPResponse:
        """Execute single request"""
        async with self._semaphore:
            headers = self._fingerprint_manager.get_realistic_headers(config.url)

            if config.headers:
                headers.update(config.headers)

            # Prepare request kwargs
            kwargs = {
                "method": config.method,
                "url": config.url,
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=config.timeout),
                "ssl": config.verify_ssl,
                "allow_redirects": config.allow_redirects,
                "proxy": config.proxy if config.use_proxy else None
            }

            if config.params:
                kwargs["params"] = config.params

            if config.json_data:
                kwargs["json"] = config.json_data
            elif config.data:
                kwargs["data"] = config.data

            # Execute request
            async with self._session.request(**kwargs) as response:
                body = await response.read()

                # Update stats
                self.stats["total_bytes_sent"] += sum(
                    len(k) + len(v) for k, v in headers.items()
                )
                self.stats["total_bytes_recv"] += len(body)

                # Build response
                http_response = HTTPResponse(
                    url=str(response.url),
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=body,
                    response_time_ms=0,  # Will be set by caller
                    state=ResponseState.UNKNOWN
                )

                # Detect state
                if response.status == 200:
                    http_response.state = ResponseState.SUCCESS
                elif response.status == 403:
                    http_response.state = ResponseState.BLOCKED
                elif response.status == 429:
                    http_response.state = ResponseState.RATE_LIMITED
                else:
                    http_response.state = ResponseState.SUCCESS

                # Detect WAF
                http_response.waf_detected = WAFDetector.detect(http_response)
                if http_response.waf_detected:
                    http_response.state = ResponseState.WAF_BLOCK

                # Identify technologies
                http_response.technologies = self._identify_technologies(
                    http_response.headers, body
                )

                return http_response

    def _identify_technologies(
        self,
        headers: Dict[str, str],
        body: bytes
    ) -> List[str]:
        """Identify server technologies from response"""
        technologies = []
        headers_str = str(headers).lower()
        body_str = body.decode('utf-8', errors='ignore').lower()

        # Server header
        server = headers.get('Server', headers.get('server', ''))
        if server:
            technologies.append(f"Server: {server}")

        # Powered by
        powered = headers.get('X-Powered-By', headers.get('x-powered-by', ''))
        if powered:
            technologies.append(f"Powered: {powered}")

        # CDN detection
        cdn_headers = [
            ('cf-ray', 'Cloudflare'),
            ('x-akamai', 'Akamai'),
            ('x-cdn', 'CDN'),
            ('x-sucuri-id', 'Sucuri')
        ]
        for header, cdn in cdn_headers:
            if header in headers_str:
                technologies.append(f"CDN: {cdn}")

        # CMS detection from body
        cms_patterns = [
            ('wp-content', 'WordPress'),
            ('drupal', 'Drupal'),
            ('joomla', 'Joomla'),
            ('magento', 'Magento'),
            ('shopify', 'Shopify'),
            ('react', 'React'),
            ('vue', 'Vue.js'),
            ('angular', 'Angular')
        ]
        for pattern, name in cms_patterns:
            if pattern in body_str:
                technologies.append(f"CMS: {name}")

        # Security headers
        security_headers = [
            ('x-frame-options', 'X-Frame-Options'),
            ('content-security-policy', 'CSP'),
            ('strict-transport-security', 'HSTS'),
            ('x-content-type-options', 'X-Content-Type-Options')
        ]
        for header, name in security_headers:
            if header in headers_str:
                technologies.append(f"Security: {name}")

        return technologies

    async def get(self, url: str, **kwargs) -> HTTPResponse:
        """Quick GET request"""
        config = RequestConfig(url=url, method="GET", **kwargs)
        return await self.request(config)

    async def post(self, url: str, **kwargs) -> HTTPResponse:
        """Quick POST request"""
        config = RequestConfig(url=url, method="POST", **kwargs)
        return await self.request(config)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            "success_rate": self.stats["requests_success"] / max(self.stats["requests_total"], 1),
            "block_rate": self.stats["requests_blocked"] / max(self.stats["requests_total"], 1)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION POOL MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConnectionPoolManager:
    """
    Manages multiple HTTP clients as a pool

    Features:
    - Round-robin selection
    - Least-connections selection
    - Per-host pools
    - Automatic cleanup
    """

    def __init__(self, pool_size: int = 5, **kwargs):
        self.pool_size = pool_size
        self.default_kwargs = kwargs
        self._pools: List[HTTPClient] = []
        self._current_index = 0
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        """Initialize pool"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup pool"""
        await self.cleanup()

    async def initialize(self) -> None:
        """Create client pool"""
        async with self._lock:
            if self._pools:
                return

            for _ in range(self.pool_size):
                client = HTTPClient(**self.default_kwargs)
                await client.initialize()
                self._pools.append(client)

    async def cleanup(self) -> None:
        """Cleanup all clients"""
        async with self._lock:
            for client in self._pools:
                await client.cleanup()
            self._pools.clear()

    async def get_client(self) -> HTTPClient:
        """Get next client using round-robin"""
        async with self._lock:
            client = self._pools[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._pools)
            return client

    async def request(self, config: RequestConfig) -> HTTPResponse:
        """Route request to pool"""
        client = await self.get_client()
        return await client.request(config)

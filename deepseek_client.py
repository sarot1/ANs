"""
R1X Platform - DeepSeek AI Integration
واجهة دمج DeepSeek-Coder-V2 API
Version: 3.0.0

وظائف هذا الملف:
- الاتصال بـ DeepSeek API
- تحليل الاستجابات من WAF
- توليد خطط بديلة ذكية
- تعديل البصمة تلقائياً
- التعلم من المحاولات السابقة
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

import aiohttp


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class DeepSeekConfig:
    """إعدادات DeepSeek API"""

    # API Configuration
    API_KEY: str = "sk-43fa71eb41674587a7ca28c0392e5cf3"
    BASE_URL: str = "https://api.deepseek.com/v1"
    MODEL: str = "deepseek-coder"

    # Generation Settings
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9

    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    TIMEOUT: float = 30.0

    # Cache Settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 hour


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisType(Enum):
    """نوع التحليل المطلوب"""
    WAF_BYPASS = "waf_bypass"           # تحليل تجاوز WAF
    PAYLOAD_GENERATION = "payload_generation"  # توليد payloads
    ENDPOINT_ANALYSIS = "endpoint_analysis"    # تحليلEndpoints
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"  # تقييم ثغرات
    FINGERPRINT_ADAPTATION = "fingerprint_adaptation"  # تكييف البصمة
    ALTERNATIVE_PATHS = "alternative_paths"  # توليد مسارات بديلة


@dataclass
class DeepSeekResponse:
    """استجابة DeepSeek API"""
    success: bool
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    response_time_ms: float = 0.0
    error: Optional[str] = None
    cached: bool = False


@dataclass
class BypassPlanFromAI:
    """خطة تجاوز من DeepSeek AI"""
    plan_id: str
    plan_name: str
    description: str
    techniques: List[str]
    headers_to_modify: Dict[str, str]
    payload_modifications: Optional[Dict[str, Any]]
    timing_strategy: Dict[str, Any]
    confidence_score: float
    reasoning: str
    success_criteria: List[str]


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

class PromptTemplates:
    """قوالب الأوامر لـ DeepSeek"""

    @staticmethod
    def waf_bypass_prompt(
        target: str,
        waf_type: str,
        block_response: str,
        attempted_techniques: List[str]
    ) -> str:
        """أمر توليد خطة تجاوز WAF"""
        return f"""
# مهمة: توليد خطة تجاوز WAF ذكية

## الهدف
توليد 3 خطط بديلة لتجاوز {waf_type} على الهدف: {target}

## المعلومات المتاحة
- الهدف: {target}
- نوع WAF: {waf_type}
- استجابة الحظر: {block_response[:500]}
- التقنيات التي تم تجربتها: {', '.join(attempted_techniques) if attempted_techniques else 'لا شيء'}

## المتطلبات
لكل خطة قدم:
1. معرف فريد (PLAN_A, PLAN_B, PLAN_C)
2. اسم الخطة
3. وصف مختصر
4. التقنيات المستخدمة (قائمة)
5. تعديلات الهيدرز المطلوبة
6. تعديلات الـ Payload إن وجدت
7. استراتيجية التوقيت
8. مستوى الثقة (0.0 - 1.0)
9. منطق الخطة (لماذا ستعمل)

## صيغة الرد المتوقعة
أرجع JSON بهذا الشكل:
```json
{{
  "plans": [
    {{
      "plan_id": "PLAN_A",
      "plan_name": "اسم الخطة",
      "techniques": ["technique1", "technique2"],
      "headers_modifications": {{"Header": "Value"}},
      "confidence_score": 0.85,
      "reasoning": "..."
    }}
  ]
}}
```

## ملاحظات مهمة
- لا تكرر التقنيات الفاشلة
- ركز على تقنيات غير تقليدية
- اضمن أن كل خطة مختلفة عن الأخرى
"""

    @staticmethod
    def alternative_paths_prompt(
        target: str,
        current_path: str,
        block_reason: str,
        available_endpoints: List[str]
    ) -> str:
        """أمر توليد مسارات بديلة"""
        return f"""
# مهمة: توليد مسارات بديلة للوصول للهدف

## الهدف
{target}

## المسار الحالي المحظور
{current_path}

## سبب الحظر
{block_reason}

## نقاط النهاية المتاحة
{', '.join(available_endpoints[:20]) if available_endpoints else 'غير متاحة'}

## المتطلبات
توليد 3 مسارات بديلة:
1. مسار باستخدام نقاط النهاية المتاحة
2. مسار باستخدام تقنيات URL manipulation
3. مسار باستخدام ترتيب مختلف للـ headers

أرجع JSON:
```json
{{
  "paths": [
    {{
      "path": "المسار الكامل",
      "technique": " technique المستخدمة",
      "headers": {{}},
      "confidence": 0.9
    }}
  ]
}}
```
"""

    @staticmethod
    def fingerprint_adaptation_prompt(
        target: str,
        current_fingerprint: str,
        waf_type: str,
        failed_attempts: List[str]
    ) -> str:
        """أمر تكييف البصمة"""
        return f"""
# مهمة: توليد بصمة جديدة لتجاوزDetection

## الهدف
{target}

## البصمة الحالية
{current_fingerprint}

## نوع WAF المكتشف
{waf_type}

## المحاولات الفاشلة
{', '.join(failed_attempts) if failed_attempts else 'لا شيء'}

## المتطلبات
توليد بصمة جديدة تتضمن:
1. User-Agent جديد
2. Header order مختلف
3. TLS fingerprint مختلف
4. Timing pattern خاص

أرجع JSON:
```json
{{
  "new_fingerprint": {{
    "user_agent": "...",
    "headers_order": [...],
    "tls_profile": "...",
    "timing_pattern": {{"delay_ms": 100, "jitter": 20}},
    "reasoning": "..."
  }}
}}
```
"""

    @staticmethod
    def vulnerability_analysis_prompt(
        endpoint: str,
        response: str,
        technologies: List[str]
    ) -> str:
        """أمر تحليل الثغرات"""
        return f"""
# مهمة: تحليل نقطة نهاية للثغرات المحتملة

## Endpoint
{endpoint}

## Technologies المكتشفة
{', '.join(technologies) if technologies else 'غير محددة'}

## الاستجابة (أول 1000 حرف)
{response[:1000]}

## المتطلبات
حدد:
1. نوع الثغرات المحتملة
2. Payload المناسب للاختبار
3. طريقة الاستغلال
4. مستوى الخطورة

أرجع JSON:
```json
{{
  "vulnerabilities": [
    {{
      "type": "sql_injection",
      "payload": "...",
      "exploitation": "...",
      "severity": "high"
    }}
  ]
}}
```
"""


# ═══════════════════════════════════════════════════════════════════════════════
# DEEPSEEK CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class DeepSeekClient:
    """
    🤖 DeepSeek AI Client - العقل المدبر

    الميزات:
    - تحليل استجابات WAF ذكي
    - توليد خطط بديلة متعددة
    - تكييف البصمة تلقائياً
    - تعلم من المحاولات السابقة
    - تخزين مؤقت للاستجابات
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or DeepSeekConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, DeepSeekResponse] = {}
        self._request_history: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_cached": 0,
            "requests_failed": 0,
            "total_tokens": 0
        }

    async def __aenter__(self):
        """Initialize session"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup session"""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if self._session:
            return

        timeout = aiohttp.ClientTimeout(total=self.config.TIMEOUT)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self) -> None:
        """Cleanup HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_cache_key(self, prompt: str, analysis_type: AnalysisType) -> str:
        """Get cache key for prompt"""
        content = f"{analysis_type.value}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def _make_request(
        self,
        prompt: str,
        analysis_type: AnalysisType
    ) -> DeepSeekResponse:
        """Make API request to DeepSeek"""
        start_time = time.time()

        # Check cache
        cache_key = self._get_cache_key(prompt, analysis_type)
        if self.config.ENABLE_CACHE and cache_key in self._cache:
            cached_response = self._cache[cache_key]
            cached_response.cached = True
            self.stats["requests_cached"] += 1
            return cached_response

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.config.API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.MODEL,
            "messages": [
                {"role": "system", "content": "You are a security researcher specialized in web application security and WAF bypass techniques."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.MAX_TOKENS,
            "temperature": self.config.TEMPERATURE,
            "top_p": self.config.TOP_P
        }

        # Make request with retry
        last_error = None
        for attempt in range(self.config.MAX_RETRIES):
            try:
                async with self._session.post(
                    f"{self.config.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})

                        result = DeepSeekResponse(
                            success=True,
                            content=content,
                            model=data.get("model", self.config.MODEL),
                            usage={
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                                "total_tokens": usage.get("total_tokens", 0)
                            },
                            response_time_ms=(time.time() - start_time) * 1000
                        )

                        # Cache result
                        if self.config.ENABLE_CACHE:
                            self._cache[cache_key] = result

                        # Update stats
                        self.stats["requests_total"] += 1
                        self.stats["requests_success"] += 1
                        self.stats["total_tokens"] += usage.get("total_tokens", 0)

                        # Record history
                        self._request_history.append({
                            "type": analysis_type.value,
                            "timestamp": time.time(),
                            "tokens": usage.get("total_tokens", 0),
                            "success": True
                        })

                        return result

                    elif response.status == 429:
                        # Rate limited - wait and retry
                        await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                        last_error = "Rate limited"
                        continue

                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"
                        continue

            except asyncio.TimeoutError:
                last_error = "Request timeout"
                await asyncio.sleep(self.config.RETRY_DELAY)
                continue

            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(self.config.RETRY_DELAY)
                continue

        # All retries failed
        result = DeepSeekResponse(
            success=False,
            content="",
            model=self.config.MODEL,
            error=last_error,
            response_time_ms=(time.time() - start_time) * 1000
        )

        self.stats["requests_total"] += 1
        self.stats["requests_failed"] += 1

        return result

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC METHODS - ANALYSIS TYPES
    # ═══════════════════════════════════════════════════════════════════════

    async def analyze_waf_and_generate_bypass_plans(
        self,
        target: str,
        waf_type: str,
        block_response: str,
        attempted_techniques: Optional[List[str]] = None
    ) -> List[BypassPlanFromAI]:
        """
        تحليل WAF وتوليد خطط تجاوز متعددة

        Args:
            target: الهدف المراد فحصه
            waf_type: نوع WAF المكتشف
            block_response: استجابة الحظر
            attempted_techniques: التقنيات التي تم تجربتها

        Returns:
            قائمة بـ 3 خطط بديلة
        """
        attempted = attempted_techniques or []

        prompt = PromptTemplates.waf_bypass_prompt(
            target=target,
            waf_type=waf_type,
            block_response=block_response,
            attempted_techniques=attempted
        )

        response = await self._make_request(prompt, AnalysisType.WAF_BYPASS)

        if not response.success:
            return self._generate_fallback_plans(target, waf_type)

        try:
            # Parse JSON response
            json_match = response.content.find("```json")
            if json_match != -1:
                json_str = response.content[json_match+7:]
                json_end = json_str.find("```")
                if json_end != -1:
                    json_str = json_str[:json_end]
                data = json.loads(json_str.strip())
            else:
                data = json.loads(response.content)

            plans = []
            for i, plan_data in enumerate(data.get("plans", [])[:3]):
                plan = BypassPlanFromAI(
                    plan_id=plan_data.get("plan_id", f"PLAN_{['A','B','C'][i]}"),
                    plan_name=plan_data.get("plan_name", f"Plan {['A','B','C'][i]}"),
                    description=plan_data.get("description", ""),
                    techniques=plan_data.get("techniques", []),
                    headers_to_modify=plan_data.get("headers_modifications", {}),
                    payload_modifications=plan_data.get("payload_modifications"),
                    timing_strategy=plan_data.get("timing_strategy", {}),
                    confidence_score=plan_data.get("confidence_score", 0.5),
                    reasoning=plan_data.get("reasoning", ""),
                    success_criteria=plan_data.get("success_criteria", [])
                )
                plans.append(plan)

            return plans if plans else self._generate_fallback_plans(target, waf_type)

        except json.JSONDecodeError:
            return self._generate_fallback_plans(target, waf_type)

    async def generate_alternative_paths(
        self,
        target: str,
        current_path: str,
        block_reason: str,
        available_endpoints: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        توليد مسارات بديلة للوصول للهدف

        Args:
            target: الهدف
            current_path: المسار المحظور
            block_reason: سبب الحظر
            available_endpoints: نقاط النهاية المتاحة

        Returns:
            قائمة المسارات البديلة
        """
        prompt = PromptTemplates.alternative_paths_prompt(
            target=target,
            current_path=current_path,
            block_reason=block_reason,
            available_endpoints=available_endpoints or []
        )

        response = await self._make_request(prompt, AnalysisType.ALTERNATIVE_PATHS)

        if not response.success:
            return self._generate_fallback_paths(target)

        try:
            json_match = response.content.find("```json")
            if json_match != -1:
                json_str = response.content[json_match+7:]
                json_end = json_str.find("```")
                if json_end != -1:
                    json_str = json_str[:json_end]
                data = json.loads(json_str.strip())
            else:
                data = json.loads(response.content)

            return data.get("paths", [])[:3]

        except json.JSONDecodeError:
            return self._generate_fallback_paths(target)

    async def generate_adaptive_fingerprint(
        self,
        target: str,
        current_fingerprint: str,
        waf_type: str,
        failed_attempts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        توليد بصمة جديدة تكيّفية

        Args:
            target: الهدف
            current_fingerprint: البصمة الحالية
            waf_type: نوع WAF
            failed_attempts: المحاولات الفاشلة

        Returns:
            بيانات البصمة الجديدة
        """
        prompt = PromptTemplates.fingerprint_adaptation_prompt(
            target=target,
            current_fingerprint=current_fingerprint,
            waf_type=waf_type,
            failed_attempts=failed_attempts or []
        )

        response = await self._make_request(prompt, AnalysisType.FINGERPRINT_ADAPTATION)

        if not response.success:
            return self._generate_fallback_fingerprint()

        try:
            json_match = response.content.find("```json")
            if json_match != -1:
                json_str = response.content[json_match+7:]
                json_end = json_str.find("```")
                if json_end != -1:
                    json_str = json_str[:json_end]
                data = json.loads(json_str.strip())
            else:
                data = json.loads(response.content)

            return data.get("new_fingerprint", {})

        except json.JSONDecodeError:
            return self._generate_fallback_fingerprint()

    async def analyze_vulnerability(
        self,
        endpoint: str,
        response: str,
        technologies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        تحليل الثغرات المحتملة في endpoint

        Args:
            endpoint: نقطة النهاية
            response: استجابة الخادم
            technologies: التقنيات المكتشفة

        Returns:
            قائمة الثغرات المحتملة
        """
        prompt = PromptTemplates.vulnerability_analysis_prompt(
            endpoint=endpoint,
            response=response,
            technologies=technologies or []
        )

        response_ai = await self._make_request(prompt, AnalysisType.VULNERABILITY_ASSESSMENT)

        if not response_ai.success:
            return []

        try:
            json_match = response_ai.content.find("```json")
            if json_match != -1:
                json_str = response_ai.content[json_match+7:]
                json_end = json_str.find("```")
                if json_end != -1:
                    json_str = json_str[:json_end]
                data = json.loads(json_str.strip())
            else:
                data = json.loads(response_ai.content)

            return data.get("vulnerabilities", [])

        except json.JSONDecodeError:
            return []

    # ═══════════════════════════════════════════════════════════════════════
    # FALLBACK METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_fallback_plans(
        self,
        target: str,
        waf_type: str
    ) -> List[BypassPlanFromAI]:
        """توليد خطط بديلة افتراضية"""
        import random

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]

        return [
            BypassPlanFromAI(
                plan_id="PLAN_A",
                plan_name="Conservative Header Rotation",
                description="تدوير بسيط للـ Headers",
                techniques=["header_rotation", "user_agent_swap"],
                headers_to_modify={
                    "User-Agent": random.choice(user_agents),
                    "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "Accept-Language": "en-US,en;q=0.9"
                },
                payload_modifications=None,
                timing_strategy={"delay_ms": 500, "jitter": 100},
                confidence_score=0.6,
                reasoning="تقنية محافظة تستخدم تدوير الـ User-Agent",
                success_criteria=["status_200", "no_waf_block"]
            ),
            BypassPlanFromAI(
                plan_id="PLAN_B",
                plan_name="Protocol Obfuscation",
                description="تغيير مستوى البروتوكول",
                techniques=["http_downgrade", "header_permutation"],
                headers_to_modify={
                    "User-Agent": random.choice(user_agents),
                    "HTTP-Version": "HTTP/1.0",
                    "Connection": "keep-alive",
                    "X-Requested-With": "XMLHttpRequest"
                },
                payload_modifications={"double_encoding": True},
                timing_strategy={"delay_ms": 1000, "jitter": 200},
                confidence_score=0.5,
                reasoning="تخفيض HTTP قد يتجاوز بعض الـ WAF",
                success_criteria=["status_200", "content_length > 100"]
            ),
            BypassPlanFromAI(
                plan_id="PLAN_C",
                plan_name="Aggressive Multi-Vector",
                description="تقنيات متعددة متقدمة",
                techniques=["fragmentation", "timing_manipulation", "encoding_variation"],
                headers_to_modify={
                    "User-Agent": random.choice(user_agents),
                    "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "CF-Connecting-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "True-Client-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                },
                payload_modifications={"fragment_payload": True},
                timing_strategy={"delay_ms": 2000, "jitter": 500},
                confidence_score=0.4,
                reasoning="محاولة مكثفة بتقنيات متعددة",
                success_criteria=["status_200", "no_block_page"]
            )
        ]

    def _generate_fallback_paths(self, target: str) -> List[Dict[str, Any]]:
        """توليد مسارات بديلة افتراضية"""
        return [
            {
                "path": f"{target}/?parameter=value",
                "technique": "query_parameter_insertion",
                "headers": {"X-Forwarded-For": "127.0.0.1"},
                "confidence": 0.7
            },
            {
                "path": f"{target}/./path",
                "technique": "path_traversal_obfuscation",
                "headers": {},
                "confidence": 0.5
            },
            {
                "path": f"{target}//path",
                "technique": "double_slash_bypass",
                "headers": {"User-Agent": "Mozilla/5.0"},
                "confidence": 0.6
            }
        ]

    def _generate_fallback_fingerprint(self) -> Dict[str, Any]:
        """توليد بصمة افتراضية"""
        import random

        return {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "headers_order": ["Host", "User-Agent", "Accept", "Accept-Language", "Accept-Encoding", "Connection", "Cache-Control"],
            "tls_profile": "chrome_120_tls_13",
            "timing_pattern": {
                "delay_ms": random.randint(100, 500),
                "jitter": random.randint(10, 100)
            }
        }

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            "cache_size": len(self._cache),
            "history_size": len(self._request_history),
            "cache_hit_rate": self.stats["requests_cached"] / max(self.stats["requests_total"], 1),
            "success_rate": self.stats["requests_success"] / max(self.stats["requests_total"], 1)
        }

    def clear_cache(self) -> None:
        """Clear response cache"""
        self._cache.clear()

    async def health_check(self) -> bool:
        """Check if API is accessible"""
        try:
            test_prompt = "Hello, respond with 'OK'"
            response = await self._make_request(test_prompt, AnalysisType.WAF_BYPASS)
            return response.success
        except Exception:
            return False
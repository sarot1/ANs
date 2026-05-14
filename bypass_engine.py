"""
R1X Platform - WAF Bypass Engine with DeepSeek AI
القلب النابض - تجاوز جدران الحماية بالذكاء الاصطناعي
Version: 3.0.0

التحديثات:
- دمج DeepSeek AI للتحليل والتخطيط
- توليد خطط بديلة ذكية
- تكييف البصمة تلقائياً
- تعلم من المحاولات السابقة
- تقليل المحاولات الفاشلة
"""

import asyncio
import time
import random
import hashlib
import re
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy

from core.constants import (
    BYPASS_TECHNIQUES, USER_AGENTS, WAFType, BlockType
)
from core.exceptions import BypassExhaustedError
from modules.network.http_client import HTTPClient, RequestConfig, WAFDetector, HTTPResponse


# ═══════════════════════════════════════════════════════════════════════════════
# BYPASS TECHNIQUES ENUM
# ═══════════════════════════════════════════════════════════════════════════════

class BypassTechnique(Enum):
    """Categories of bypass techniques"""
    HEADER_ROTATION = "header_rotation"
    PROTOCOL_OBFUSCATION = "protocol_obfuscation"
    TIMING_ATTACK = "timing_attack"
    ENCODING_EVASION = "encoding_evasion"
    FRAGMENTATION = "fragmentation"
    PROXY_ROTATION = "proxy_rotation"
    IP_ROTATION = "ip_rotation"
    SESSION_MANIPULATION = "session_manipulation"
    PAYLOAD_SPLITTING = "payload_splitting"
    CHUNKED_TRANSFER = "chunked_transfer"
    HTTP_VERSION_SWITCH = "http_version_switch"
    ENCODING_VARIATION = "encoding_variation"
    AI_GENERATED = "ai_generated"  # New - من DeepSeek


class PlanComplexity(Enum):
    """Complexity level of bypass plan"""
    LOW = "low"           # Simple modifications
    MEDIUM = "medium"     # Moderate evasion
    HIGH = "high"         # Advanced techniques
    CRITICAL = "critical"  # Extreme measures


# ═══════════════════════════════════════════════════════════════════════════════
# BYPASS PLAN
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BypassPlan:
    """
    A strategic bypass plan

    Contains:
    - Plan ID for tracking
    - List of techniques to apply
    - Confidence score (based on WAF type)
    - Execution steps
    - Expected success probability
    - Complexity level
    - Source (manual or AI)
    """
    plan_id: str
    plan_name: str
    techniques: List[BypassTechnique]
    complexity: PlanComplexity
    confidence_score: float  # 0.0 to 1.0
    execution_steps: List[str] = field(default_factory=list)
    headers_modifications: Dict[str, str] = field(default_factory=dict)
    payload_modifications: Optional[Dict[str, Any]] = None
    delay_range_ms: Tuple[int, int] = (0, 0)
    required_tools: List[str] = field(default_factory=list)
    fallback_plan_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "manual"  # "manual" or "ai"
    ai_reasoning: Optional[str] = None

    def __repr__(self) -> str:
        return f"BypassPlan({self.plan_id}): {self.plan_name} ({self.complexity.value}) - {self.confidence_score:.0%} [Source: {self.source}]"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "techniques": [t.value for t in self.techniques],
            "complexity": self.complexity.value,
            "confidence_score": self.confidence_score,
            "execution_steps": self.execution_steps,
            "delay_range_ms": self.delay_range_ms,
            "fallback_plan_id": self.fallback_plan_id,
            "metadata": self.metadata,
            "source": self.source,
            "ai_reasoning": self.ai_reasoning
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BYPASS ENGINE WITH DEEPSEEK AI
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BypassContext:
    """Context of current bypass attempt"""
    target: str
    original_request: RequestConfig
    block_response: HTTPResponse
    detected_waf: Optional[str]
    block_type: BlockType
    attempt_number: int = 0
    failed_techniques: List[str] = field(default_factory=list)
    successful_techniques: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    scan_id: Optional[str] = None  # For DeepSeek integration
    brain: Optional[Any] = None  # VIPX1Brain instance


@dataclass
class BypassResult:
    """Result of bypass attempt"""
    success: bool
    plan_id: Optional[str]
    technique_used: Optional[str]
    response: Optional[HTTPResponse]
    bypass_successful: bool = False
    response_time_ms: float = 0.0
    attempts_made: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    ai_generated: bool = False


class WAFBypassEngine:
    """
    💓 القلب النابض - WAF Bypass Engine with DeepSeek AI

    الميزات الأساسية:
    1. Detection متعددة لأنواع WAF
    2. Generation ذكي ل Plans بديلة (يدوي + AI)
    3. Execution متتابع لل Plans
    4. Learning من النتائج السابقة
    5. Adaptive modification للتكتيكات
    6. DeepSeek AI integration للتخطيط الذكي ⭐

    workflow:
    1. Detect WAF type
    2. Try manual plans first (A, B, C)
    3. If all fail → Ask DeepSeek AI for new plans
    4. Execute AI-generated plans
    5. Learn from outcome → Update confidence scores
    """

    def __init__(self, http_client: HTTPClient, brain: Optional[Any] = None):
        self.http_client = http_client
        self.brain = brain  # VIPX1Brain for DeepSeek integration
        self._plan_counter = 0
        self._plan_history: List[BypassPlan] = []
        self._technique_effectiveness: Dict[str, float] = {}
        self._ai_plans_cache: Dict[str, List[BypassPlan]] = {}

        # WAF-specific technique mappings
        self._waf_technique_map = self._build_waf_map()

        # Initialize default effectiveness scores
        for technique in BypassTechnique:
            self._technique_effectiveness[technique.value] = 0.5

    def _build_waf_map(self) -> Dict[str, Dict[str, Any]]:
        """Build WAF-specific bypass strategy mappings"""
        return {
            "cloudflare": {
                "primary_techniques": [
                    BypassTechnique.HEADER_ROTATION,
                    BypassTechnique.PROTOCOL_OBFUSCATION,
                    BypassTechnique.TIMING_ATTACK
                ],
                "confidence_base": 0.75,
                "recommended_delay": (5000, 15000),
                "specific_bypass": [
                    "Use non-standard HTTP methods",
                    "Rotate User-Agent to mobile browser",
                    "Add cf-ray header manipulation",
                    "Use HTTP/1.0 instead of HTTP/1.1",
                    "Add X-Forwarded-For with sequential IPs"
                ]
            },
            "akamai": {
                "primary_techniques": [
                    BypassTechnique.ENCODING_EVASION,
                    BypassTechnique.FRAGMENTATION,
                    BypassTechnique.PROXY_ROTATION
                ],
                "confidence_base": 0.70,
                "recommended_delay": (3000, 10000),
                "specific_bypass": [
                    "Double URL encoding",
                    "Unicode normalization",
                    "Use residential proxy",
                    "Fragment payload across requests"
                ]
            },
            "imperva": {
                "primary_techniques": [
                    BypassTechnique.PAYLOAD_SPLITTING,
                    BypassTechnique.ENCODING_VARIATION,
                    BypassTechnique.HEADER_ROTATION
                ],
                "confidence_base": 0.65,
                "recommended_delay": (10000, 30000),
                "specific_bypass": [
                    "Split payload into multiple parameters",
                    "Use mixed encoding (URL + Unicode)",
                    "Add duplicate headers",
                    "Use charset variation"
                ]
            },
            "aws_waf": {
                "primary_techniques": [
                    BypassTechnique.TIMING_ATTACK,
                    BypassTechnique.SESSION_MANIPULATION,
                    BypassTechnique.PROXY_ROTATION
                ],
                "confidence_base": 0.80,
                "recommended_delay": (2000, 5000),
                "specific_bypass": [
                    "Implement exponential backoff",
                    "Use different AWS IP ranges",
                    "Rotate session cookies",
                    "Add AWS-specific headers"
                ]
            },
            "f5_bigip": {
                "primary_techniques": [
                    BypassTechnique.CHUNKED_TRANSFER,
                    BypassTechnique.HTTP_VERSION_SWITCH,
                    BypassTechnique.HEADER_ROTATION
                ],
                "confidence_base": 0.60,
                "recommended_delay": (3000, 8000),
                "specific_bypass": [
                    "Use chunked transfer encoding",
                    "Downgrade to HTTP/1.0",
                    "Remove Transfer-Encoding header",
                    "Add malformed headers"
                ]
            },
            "generic_waf": {
                "primary_techniques": [
                    BypassTechnique.HEADER_ROTATION,
                    BypassTechnique.TIMING_ATTACK,
                    BypassTechnique.ENCODING_EVASION
                ],
                "confidence_base": 0.50,
                "recommended_delay": (5000, 20000),
                "specific_bypass": [
                    "Randomize all headers",
                    "Add delay between requests",
                    "Use double encoding"
                ]
            }
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PLAN GENERATION (Manual + AI)
    # ═══════════════════════════════════════════════════════════════════════

    async def generate_bypass_plans(
        self,
        context: BypassContext,
        count: int = 3
    ) -> List[BypassPlan]:
        """
        Generate bypass plans (manual first, then AI if needed)

        Args:
            context: Current bypass context
            count: Number of plans to generate

        Returns:
            List of bypass plans
        """
        waf_type = context.detected_waf or "generic_waf"
        waf_config = self._waf_technique_map.get(waf_type, self._waf_technique_map["generic_waf"])

        plans = []

        # Plan A: Conservative (Manual)
        plan_a = await self._generate_conservative_plan(context, waf_config)
        plans.append(plan_a)

        # Plan B: Balanced (Manual)
        plan_b = await self._generate_balanced_plan(context, waf_config)
        plans.append(plan_b)

        # Plan C: Aggressive (Manual)
        plan_c = await self._generate_aggressive_plan(context, waf_config)
        plans.append(plan_c)

        # Set fallback chain
        if len(plans) >= 2:
            plans[0].fallback_plan_id = plans[1].plan_id
        if len(plans) >= 3:
            plans[1].fallback_plan_id = plans[2].plan_id

        self._plan_history.extend(plans)
        return plans[:count]

    async def generate_ai_plans(
        self,
        context: BypassContext,
        count: int = 3
    ) -> List[BypassPlan]:
        """
        Generate bypass plans using DeepSeek AI ⭐

        This is called when manual plans fail and we need
        intelligent, adaptive planning from DeepSeek.

        Args:
            context: Current bypass context
            count: Number of plans to generate

        Returns:
            List of AI-generated bypass plans
        """
        if not self.brain:
            print("⚠️ DeepSeek AI not available, using fallback plans")
            return await self.generate_fallback_plans(context)

        try:
            # Get AI-generated plans from Brain
            ai_plans = await self.brain.analyze_block_and_generate_plans(
                scan_id=context.scan_id or "unknown",
                target=context.target,
                waf_type=context.detected_waf or "generic_waf",
                block_response=context.block_response.body_text[:500],
                attempted_techniques=context.failed_techniques
            )

            # Convert AI plans to BypassPlan objects
            bypass_plans = []
            for i, ai_plan in enumerate(ai_plans[:count]):
                plan = BypassPlan(
                    plan_id=f"AI_PLAN_{i+1}",
                    plan_name=ai_plan.plan_name,
                    techniques=[BypassTechnique.HEADER_ROTATION],  # Default
                    complexity=PlanComplexity.MEDIUM,
                    confidence_score=ai_plan.confidence_score,
                    execution_steps=[ai_plan.description],
                    headers_modifications=ai_plan.headers_to_modify,
                    payload_modifications=ai_plan.payload_modifications,
                    delay_range_ms=(ai_plan.timing_strategy.get("delay_ms", 1000), 2000),
                    metadata={"ai_plan": ai_plan.to_dict() if hasattr(ai_plan, 'to_dict') else {}},
                    source="ai",
                    ai_reasoning=ai_plan.reasoning if hasattr(ai_plan, 'reasoning') else ""
                )
                bypass_plans.append(plan)

            # Cache AI plans for this target+waf combination
            cache_key = f"{context.target}:{context.detected_waf}"
            self._ai_plans_cache[cache_key] = bypass_plans

            return bypass_plans

        except Exception as e:
            print(f"❌ AI plan generation failed: {str(e)}")
            return await self.generate_fallback_plans(context)

    async def generate_fallback_plans(
        self,
        context: BypassContext
    ) -> List[BypassPlan]:
        """Generate fallback plans when AI is unavailable"""
        return [
            BypassPlan(
                plan_id="FALLBACK_A",
                plan_name="Header Rotation Basic",
                techniques=[BypassTechnique.HEADER_ROTATION],
                complexity=PlanComplexity.LOW,
                confidence_score=0.4,
                execution_steps=["Rotate User-Agent", "Add X-Forwarded-For"],
                headers_modifications={
                    "User-Agent": self._get_alternative_ua(),
                    "X-Forwarded-For": self._generate_ip(),
                    "Accept-Language": "en-US,en;q=0.9"
                },
                delay_range_ms=(500, 1000),
                metadata={"fallback": True}
            ),
            BypassPlan(
                plan_id="FALLBACK_B",
                plan_name="HTTP Downgrade",
                techniques=[BypassTechnique.PROTOCOL_OBFUSCATION],
                complexity=PlanComplexity.MEDIUM,
                confidence_score=0.3,
                execution_steps=["Downgrade to HTTP/1.0", "Modify headers"],
                headers_modifications={
                    "HTTP-Version": "HTTP/1.0",
                    "Connection": "keep-alive"
                },
                payload_modifications={"url_encode": True},
                delay_range_ms=(1000, 2000),
                metadata={"fallback": True}
            ),
            BypassPlan(
                plan_id="FALLBACK_C",
                plan_name="Multi-IP Headers",
                techniques=[BypassTechnique.HEADER_ROTATION, BypassTechnique.IP_ROTATION],
                complexity=PlanComplexity.HIGH,
                confidence_score=0.2,
                execution_steps=["Add multiple IP headers", "Rotate IPs"],
                headers_modifications={
                    "X-Forwarded-For": self._generate_ip(),
                    "X-Real-IP": self._generate_ip(),
                    "CF-Connecting-IP": self._generate_ip(),
                    "True-Client-IP": self._generate_ip()
                },
                delay_range_ms=(2000, 4000),
                metadata={"fallback": True}
            )
        ]

    async def _generate_conservative_plan(
        self,
        context: BypassContext,
        waf_config: Dict[str, Any]
    ) -> BypassPlan:
        """Generate low-complexity, high-confidence plan"""
        self._plan_counter += 1

        techniques = waf_config.get("primary_techniques", [])[:1]
        steps = [
            f"Analyze {context.detected_waf or 'unknown WAF'} pattern",
            "Apply simple header rotation",
            "Rotate User-Agent to common browser",
            "Add randomized Accept-Language",
            "Implement minimal delay",
            "Execute request with modifications",
            "Monitor response"
        ]

        return BypassPlan(
            plan_id=f"PLAN_{self._plan_counter:03d}_A",
            plan_name="Conservative Header Rotation",
            techniques=techniques,
            complexity=PlanComplexity.LOW,
            confidence_score=waf_config.get("confidence_base", 0.6),
            execution_steps=steps,
            headers_modifications={
                "User-Agent": self._get_alternative_ua(),
                "Accept-Language": self._get_random_accept_language(),
                "X-Forwarded-For": self._generate_ip(),
                "X-Real-IP": self._generate_ip()
            },
            delay_range_ms=waf_config.get("recommended_delay", (1000, 3000)),
            metadata={"approach": "conservative", "risk": "low"},
            source="manual"
        )

    async def _generate_balanced_plan(
        self,
        context: BypassContext,
        waf_config: Dict[str, Any]
    ) -> BypassPlan:
        """Generate medium-complexity balanced plan"""
        self._plan_counter += 1

        techniques = waf_config.get("primary_techniques", [])[:2]
        steps = [
            f"Deep analysis of {context.detected_waf or 'WAF'} response",
            "Apply header permutation",
            "Modify protocol level settings",
            "Implement timing randomization",
            "Use payload encoding variation",
            "Execute with full header stack",
            "Verify bypass effectiveness"
        ]

        return BypassPlan(
            plan_id=f"PLAN_{self._plan_counter:03d}_B",
            plan_name="Balanced Multi-Layer Bypass",
            techniques=techniques,
            complexity=PlanComplexity.MEDIUM,
            confidence_score=waf_config.get("confidence_base", 0.6) * 0.9,
            execution_steps=steps,
            headers_modifications={
                "User-Agent": self._get_alternative_ua(),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "X-Forwarded-For": self._generate_ip(),
                "X-Real-IP": self._generate_ip(),
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"https://{context.target}/",
                "Origin": f"https://{context.target}"
            },
            delay_range_ms=waf_config.get("recommended_delay", (3000, 8000)),
            metadata={"approach": "balanced", "risk": "medium"},
            source="manual"
        )

    async def _generate_aggressive_plan(
        self,
        context: BypassContext,
        waf_config: Dict[str, Any]
    ) -> BypassPlan:
        """Generate high-complexity, high-reward plan"""
        self._plan_counter += 1

        techniques = waf_config.get("primary_techniques", [])[:3]
        steps = [
            f"Comprehensive analysis of {context.detected_waf or 'WAF'}",
            "Phase 1: Protocol downgrade (HTTP/1.0)",
            "Phase 2: Header injection and manipulation",
            "Phase 3: Payload fragmentation",
            "Phase 4: Timing manipulation with jitter",
            "Phase 5: Execute with all techniques combined",
            "Phase 6: Adaptive response validation",
            "Phase 7: Recovery fallback if needed"
        ]

        return BypassPlan(
            plan_id=f"PLAN_{self._plan_counter:03d}_C",
            plan_name="Aggressive Multi-Vector Assault",
            techniques=techniques,
            complexity=PlanComplexity.HIGH,
            confidence_score=waf_config.get("confidence_base", 0.6) * 0.75,
            execution_steps=steps,
            headers_modifications={
                "User-Agent": self._get_alternative_ua(mobile=True),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "X-Forwarded-For": self._generate_ip(),
                "X-Real-IP": self._generate_ip(),
                "X-Forwarded-Proto": "http",
                "X-HTTP-Method-Override": "GET",
                "Client-IP": self._generate_ip(),
                "CF-Connecting-IP": self._generate_ip(),
                "True-Client-IP": self._generate_ip(),
                "Via": "1.1 google",
                "Forwarded": f"for={self._generate_ip()};by={self._generate_ip()};host={context.target}"
            },
            delay_range_ms=waf_config.get("recommended_delay", (5000, 15000)),
            required_tools=["proxy_pool", "ua_rotator"],
            metadata={"approach": "aggressive", "risk": "high"},
            source="manual"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PLAN EXECUTION
    # ═══════════════════════════════════════════════════════════════════════

    async def execute_plan(
        self,
        context: BypassContext,
        plan: BypassPlan,
        execute_request: Callable
    ) -> BypassResult:
        """
        Execute a bypass plan

        Args:
            context: Current bypass context
            plan: Plan to execute
            execute_request: Function to execute HTTP request

        Returns:
            BypassResult with outcome
        """
        start_time = time.time()
        result = BypassResult(
            success=False,
            plan_id=plan.plan_id,
            technique_used=",".join([t.value for t in plan.techniques]),
            attempts_made=0,
            ai_generated=(plan.source == "ai")
        )

        try:
            # Apply delay if configured
            if plan.delay_range_ms[1] > 0:
                delay = random.uniform(plan.delay_range_ms[0], plan.delay_range_ms[1]) / 1000
                await asyncio.sleep(delay)

            # Build modified request
            modified_request = self._apply_plan_to_request(
                context.original_request,
                plan
            )

            # Execute request
            result.attempts_made = 1
            response = await execute_request(modified_request)
            result.response = response
            result.response_time_ms = (time.time() - start_time) * 1000

            # Check if bypass was successful
            if not WAFDetector.is_blocked(response):
                result.success = True
                result.bypass_successful = True
                context.successful_techniques.extend([t.value for t in plan.techniques])
            else:
                # Update effectiveness
                for technique in plan.techniques:
                    current = self._technique_effectiveness.get(technique.value, 0.5)
                    self._technique_effectiveness[technique.value] = current * 0.8

        except Exception as e:
            result.error = str(e)

        return result

    async def persistent_bypass(
        self,
        context: BypassContext,
        execute_request: Callable,
        max_attempts: int = 9,
        plans_per_round: int = 3
    ) -> BypassResult:
        """
        💓 Persistent Bypass with AI Integration

        Strategy:
        1. Generate 3 manual plans (A, B, C)
        2. Try Plan A → If blocked → Try Plan B → If blocked → Try Plan C
        3. If all fail → Generate 3 new AI-powered plans using DeepSeek
        4. Try AI plans
        5. If all fail → Generate more AI plans with adapted strategies
        6. Continue until success or max_attempts reached

        This is the CORE DIFFERENTIATOR of R1X:
        - Manual plans for common WAF types
        - AI-powered plans for complex bypass
        - Intelligent adaptation based on failure patterns
        - Learn from each attempt to improve next attempt
        """
        attempts = 0
        round_num = 0
        manual_rounds = 0
        ai_rounds = 0

        print(f"\n{'='*70}")
        print(f"🔥 PERSISTENT BYPASS MODE - {context.target}")
        print(f"{'='*70}")
        print(f"Block detected: {context.block_type.value}")
        if context.detected_waf:
            print(f"WAF Type: {context.detected_waf}")
        print(f"Max attempts: {max_attempts}")
        if self.brain:
            print(f"🤖 DeepSeek AI: Available")
        else:
            print(f"⚠️ DeepSeek AI: Not configured (manual mode only)")
        print(f"{'='*70}\n")

        last_result: Optional[BypassResult] = None
        use_ai = self.brain is not None

        while attempts < max_attempts:
            round_num += 1

            # Determine which plans to generate
            if use_ai and manual_rounds >= 1:
                # After first round, try AI plans
                if ai_rounds == 0:
                    print(f"\n🤖 Switching to AI-powered plan generation...")
                    plans = await self.generate_ai_plans(context, count=plans_per_round)
                    ai_rounds += 1
                else:
                    # Regenerate AI plans with adapted strategies
                    print(f"\n🤖 Generating adapted AI plans (round {ai_rounds + 1})...")
                    plans = await self.generate_ai_plans(context, count=plans_per_round)
                    ai_rounds += 1
            else:
                # Use manual plans for first round
                print(f"\n📦 ROUND {round_num}: Generating manual bypass plans")
                plans = await self.generate_bypass_plans(context, count=plans_per_round)
                if manual_rounds == 0:
                    manual_rounds = 1

            print(f"\n📦 ROUND {round_num}: Generated {len(plans)} bypass plans")

            for i, plan in enumerate(plans):
                if attempts >= max_attempts:
                    break

                plan_label = ["A", "B", "C"][i] if i < 3 else str(i+1)
                source_icon = "🤖" if plan.source == "ai" else "📋"

                print(f"\n{source_icon} Executing Plan {plan_label}: {plan.plan_name}")
                print(f"   Confidence: {plan.confidence_score:.0%}")
                print(f"   Complexity: {plan.complexity.value}")
                print(f"   Source: {plan.source}")
                print(f"   Techniques: {', '.join([t.value for t in plan.techniques])}")
                if plan.ai_reasoning:
                    print(f"   AI Reasoning: {plan.ai_reasoning[:100]}...")

                # Execute plan
                result = await self.execute_plan(context, plan, execute_request)
                last_result = result
                attempts += 1
                context.attempt_number = attempts

                if result.bypass_successful:
                    print(f"\n✅ BYPASS SUCCESSFUL!")
                    print(f"   Plan {plan_label} worked! ({source_icon})")
                    print(f"   Attempts used: {attempts}")
                    print(f"   Response time: {result.response_time_ms:.0f}ms")
                    return result

                # Log failure
                print(f"   ❌ Plan {plan_label} blocked (attempt {attempts}/{max_attempts})")

                # Add failed technique to context to avoid reusing
                for technique in plan.techniques:
                    if technique.value not in context.failed_techniques:
                        context.failed_techniques.append(technique.value)

                # Brief pause between attempts
                await asyncio.sleep(random.uniform(0.5, 1.5))

            # Brief pause between rounds
            if attempts < max_attempts:
                print(f"\n⏳ Round {round_num} complete. All plans blocked.")
                if use_ai and manual_rounds >= 1:
                    print(f"   🤖 AI mode: {ai_rounds} rounds, {attempts} total attempts")
                else:
                    print(f"   📋 Manual mode: {manual_rounds} rounds, {attempts} total attempts")
                print(f"   Generating new strategies...")
                await asyncio.sleep(random.uniform(2, 4))

        # All attempts exhausted
        print(f"\n❌ ALL {max_attempts} ATTEMPTS EXHAUSTED")
        print(f"   Target: {context.target}")
        print(f"   WAF: {context.detected_waf or 'unknown'}")
        print(f"   Manual rounds: {manual_rounds}")
        print(f"   AI rounds: {ai_rounds}")
        print(f"   Failed techniques: {', '.join(context.failed_techniques[:5])}")

        return last_result or BypassResult(
            success=False,
            plan_id=None,
            technique_used=None,
            response=None,
            bypass_successful=False,
            attempts_made=attempts,
            error="All bypass attempts exhausted"
        )

    def _apply_plan_to_request(
        self,
        original: RequestConfig,
        plan: BypassPlan
    ) -> RequestConfig:
        """Apply bypass plan modifications to request"""
        modified = RequestConfig(
            url=original.url,
            method=original.method,
            headers=original.headers.copy() if original.headers else {},
            params=original.params.copy() if original.params else None,
            data=original.data.copy() if original.data else None,
            timeout=original.timeout,
            allow_redirects=original.allow_redirects,
            verify_ssl=original.verify_ssl
        )

        # Apply header modifications
        if plan.headers_modifications:
            modified.headers.update(plan.headers_modifications)

        # Apply payload modifications based on techniques
        for technique in plan.techniques:
            if technique == BypassTechnique.ENCODING_EVASION:
                modified = self._apply_encoding_evasion(modified)
            elif technique == BypassTechnique.PROTOCOL_OBFUSCATION:
                modified = self._apply_protocol_obfuscation(modified)
            elif technique == BypassTechnique.FRAGMENTATION:
                modified = self._apply_fragmentation(modified)
            elif technique == BypassTechnique.AI_GENERATED:
                # AI plans may have custom payload modifications
                if plan.payload_modifications:
                    modified = self._apply_ai_modifications(modified, plan.payload_modifications)

        return modified

    def _apply_encoding_evasion(self, request: RequestConfig) -> RequestConfig:
        """Apply encoding evasion techniques"""
        if request.params:
            encoded_params = {}
            for k, v in request.params.items():
                encoded_params[k] = v.replace("%", "%25")  # Double encode
            request.params = encoded_params

        if request.data:
            encoded_data = {}
            for k, v in request.data.items():
                encoded_data[k] = v.replace("%", "%25")
            request.data = encoded_data

        return request

    def _apply_protocol_obfuscation(self, request: RequestConfig) -> RequestConfig:
        """Apply protocol-level obfuscation"""
        # Add protocol-specific headers
        if request.headers:
            request.headers["HTTP-Version"] = "HTTP/1.0"
            request.headers["Connection"] = "keep-alive"

        return request

    def _apply_fragmentation(self, request: RequestConfig) -> RequestConfig:
        """Apply payload fragmentation"""
        # This would split the payload across multiple requests
        # For now, just add fragmentation indicator headers
        if request.headers:
            request.headers["X-Fragment-Split"] = "true"
            request.headers["X-Request-Part"] = "1/1"

        return request

    def _apply_ai_modifications(
        self,
        request: RequestConfig,
        modifications: Dict[str, Any]
    ) -> RequestConfig:
        """Apply AI-generated payload modifications"""
        if modifications.get("double_encoding"):
            request = self._apply_encoding_evasion(request)

        if modifications.get("fragment_payload"):
            request = self._apply_fragmentation(request)

        return request

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _get_alternative_ua(self, mobile: bool = False) -> str:
        """Get alternative User-Agent"""
        if mobile:
            mobile_uas = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
            ]
            return random.choice(mobile_uas)

        # Desktop browsers
        browsers = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        return random.choice(browsers)

    def _get_random_accept_language(self) -> str:
        """Get random Accept-Language header"""
        options = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en;q=0.8",
            "de-DE,de;q=0.9,en;q=0.8",
            "fr-FR,fr;q=0.9,en;q=0.8",
            "es-ES,es;q=0.9,en;q=0.8"
        ]
        return random.choice(options)

    def _generate_ip(self) -> str:
        """Generate realistic-looking IP address"""
        # Use common IP ranges
        ip_types = [
            f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            f"10.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        ]
        return random.choice(ip_types)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get bypass engine statistics"""
        return {
            "plans_generated": self._plan_counter,
            "plans_history": len(self._plan_history),
            "ai_plans_cached": len(self._ai_plans_cache),
            "technique_effectiveness": self._technique_effectiveness,
            "most_effective_technique": max(
                self._technique_effectiveness.items(),
                key=lambda x: x[1]
            ) if self._technique_effectiveness else None,
            "ai_available": self.brain is not None
        }

    def set_brain(self, brain: Any) -> None:
        """Set the Brain instance for AI integration"""
        self.brain = brain

    def clear_cache(self) -> None:
        """Clear AI plans cache"""
        self._ai_plans_cache.clear()
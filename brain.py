"""
R1X Platform - Brain Module (الدماغ المركزي)
الربط بين DeepSeek AI و Telegram Bot
Version: 3.0.0

وظائف هذا الملف:
- ربط DeepSeek Client بـ Telegram Bot
- تنسيق العمليات بين المكونات
- إرسال التحديثات في الوقت الحقيقي
- إدارة جلسات الفحص
- معالجة الأخطاء تلقائياً
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from api.deepseek_client import DeepSeekClient, DeepSeekConfig, BypassPlanFromAI, AnalysisType
from api.telegram_bot import TelegramBot, TelegramConfig, ScanSession


# ═══════════════════════════════════════════════════════════════════════════════
# BRAIN STATES
# ═══════════════════════════════════════════════════════════════════════════════

class BrainState(Enum):
    """حالات الدماغ المركزي"""
    IDLE = "idle"                    # خامل
    INITIALIZING = "initializing"    # تهيئة
    SCANNING = "scanning"            # جاري الفحص
    ANALYZING = "analyzing"          # جاري التحليل
    BYPASSING = "bypassing"          # جاري التجاوز
    PAUSED = "paused"                # متوقف مؤقتاً
    ERROR = "error"                  # خطأ
    COMPLETED = "completed"          # مكتمل


@dataclass
class BrainConfig:
    """إعدادات الدماغ المركزي"""
    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-coder"
    deepseek_max_tokens: int = 2048

    # Telegram
    telegram_bot_token: str = ""
    admin_chat_ids: List[int] = field(default_factory=list)

    # Brain Settings
    auto_bypass: bool = True
    auto_update_telegram: bool = True
    max_bypass_rounds: int = 9
    update_interval_sec: float = 5.0

    # Retry Settings
    max_retries_on_error: int = 3
    retry_delay_sec: float = 2.0


@dataclass
class ScanContext:
    """سياق الفحص الحالي"""
    scan_id: str
    target: str
    scan_type: str
    user_id: int
    state: BrainState = BrainState.IDLE

    # Progress tracking
    current_phase: str = ""
    progress: float = 0.0
    phase_progress: float = 0.0

    # DeepSeek integration
    bypass_attempts: int = 0
    failed_techniques: List[str] = field(default_factory=list)
    generated_plans: List[BypassPlanFromAI] = field(default_factory=list)

    # Timestamps
    started_at: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)

    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    # Callbacks
    progress_callback: Optional[Callable] = None


# ═══════════════════════════════════════════════════════════════════════════════
# BRAIN MODULE
# ═══════════════════════════════════════════════════════════════════════════════

class VIPX1Brain:
    """
    🧠 الدماغ المركزي - VIPX1 Brain

    هذا هو العقل المدبر الذي يربط بين:
    - DeepSeek AI (للتحليل والتخطيط)
    - Telegram Bot (للتحكم والإشعارات)
    - Central Orchestrator (للتنفيذ)

    الميزات:
    1. تنسيق جميع المكونات
    2. إرسال تحديثات في الوقت الحقيقي
    3. معالجة الأخطاء تلقائياً
    4. توليد خطط بديلة ذكية
    5. تكييف البصمة تلقائياً
    """

    def __init__(self, config: Optional[BrainConfig] = None):
        # Configuration
        self.config = config or BrainConfig()

        # Components
        self.deepseek: Optional[DeepSeekClient] = None
        self.telegram: Optional[TelegramBot] = None

        # State
        self.state = BrainState.IDLE
        self.active_scans: Dict[str, ScanContext] = {}

        # Statistics
        self.stats = {
            "scans_started": 0,
            "scans_completed": 0,
            "scans_failed": 0,
            "bypass_attempts": 0,
            "ai_requests": 0,
            "telegram_messages": 0
        }

    # ═══════════════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════

    async def initialize(
        self,
        deepseek_api_key: Optional[str] = None,
        telegram_bot_token: Optional[str] = None
    ) -> None:
        """
        تهيئة جميع المكونات

        Args:
            deepseek_api_key: مفتاح DeepSeek API
            telegram_bot_token: مفتاح Telegram Bot
        """
        self.state = BrainState.INITIALIZING

        # Initialize DeepSeek
        deepseek_key = deepseek_api_key or self.config.deepseek_api_key
        if deepseek_key:
            deepseek_config = DeepSeekConfig()
            deepseek_config.API_KEY = deepseek_key
            deepseek_config.MODEL = self.config.deepseek_model
            deepseek_config.MAX_TOKENS = self.config.deepseek_max_tokens

            self.deepseek = DeepSeekClient(config=deepseek_config)
            await self.deepseek.initialize()

        # Initialize Telegram
        telegram_token = telegram_bot_token or self.config.telegram_bot_token
        if telegram_token:
            telegram_config = TelegramConfig()
            telegram_config.BOT_TOKEN = telegram_token
            telegram_config.ADMIN_IDS = self.config.admin_chat_ids

            self.telegram = TelegramBot(config=telegram_config, deepseek_client=self.deepseek)
            await self.telegram.initialize()

        self.state = BrainState.IDLE

    async def cleanup(self) -> None:
        """تنظيف جميع الموارد"""
        if self.deepseek:
            await self.deepseek.cleanup()

        if self.telegram:
            await self.telegram.cleanup()

        self.active_scans.clear()
        self.state = BrainState.IDLE

    # ═══════════════════════════════════════════════════════════════════════
    # SCAN MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    async def start_scan(
        self,
        target: str,
        scan_type: str,
        user_id: int,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        بدء فحص جديد مع تنسيق DeepSeek

        Args:
            target: الهدف المراد فحصه
            scan_type: نوع الفحص
            user_id: معرف المستخدم (للإشعارات)
            progress_callback: دالة الاستدعاء للتقدم

        Returns:
            معرف الفحص
        """
        import hashlib

        # Generate scan ID
        scan_id = hashlib.sha256(f"{target}:{time.time()}".encode()).hexdigest()[:12]

        # Create scan context
        context = ScanContext(
            scan_id=scan_id,
            target=target,
            scan_type=scan_type,
            user_id=user_id,
            state=BrainState.SCANNING,
            progress_callback=progress_callback
        )

        self.active_scans[scan_id] = context
        self.stats["scans_started"] += 1

        # Notify via Telegram
        if self.telegram and self.config.auto_update_telegram:
            message = f"""
🔍 *بدء فحص جديد*

📋 التفاصيل:
• الهدف: `{target}`
• النوع: `{scan_type}`
• معرف الفحص: `{scan_id}`

⏳ جاري الفحص...
"""
            await self.telegram.send_notification(user_id, message)

        # Update DeepSeek stats
        if self.deepseek:
            self.telegram.update_deepseek_stats(self.deepseek.get_statistics())

        return scan_id

    async def update_scan_progress(
        self,
        scan_id: str,
        phase: str,
        progress: float,
        message: str = ""
    ) -> None:
        """
        تحديث تقدم الفحص

        Args:
            scan_id: معرف الفحص
            phase: المرحلة الحالية
            progress: نسبة التقدم (0-100)
            message: رسالة إضافية
        """
        if scan_id not in self.active_scans:
            return

        context = self.active_scans[scan_id]
        context.current_phase = phase
        context.progress = progress
        context.last_update = time.time()

        # Send progress update via Telegram
        if self.telegram and self.config.auto_update_telegram:
            progress_bar = self._create_progress_bar(progress)
            message_text = f"""
🔄 *تقدم الفحص*

`{scan_id}`

{progress_bar}
📍 المرحلة: {phase}
⏱️ الوقت: {int(time.time() - context.started_at)}s
"""
            if message:
                message_text += f"\n📝 {message}"

            await self.telegram.send_notification(context.user_id, message_text)

        # Call progress callback
        if context.progress_callback:
            try:
                context.progress_callback(progress, phase, message)
            except Exception:
                pass

    async def complete_scan(
        self,
        scan_id: str,
        results: Dict[str, Any],
        success: bool = True
    ) -> None:
        """
        إكمال الفحص

        Args:
            scan_id: معرف الفحص
            results: نتائج الفحص
            success: هل الفحص نجح
        """
        if scan_id not in self.active_scans:
            return

        context = self.active_scans[scan_id]
        context.results = results
        context.last_update = time.time()

        if success:
            context.state = BrainState.COMPLETED
            self.stats["scans_completed"] += 1
        else:
            context.state = BrainState.ERROR
            self.stats["scans_failed"] += 1

        # Send completion notification
        if self.telegram and self.config.auto_update_telegram:
            vuln_count = len(results.get("vulnerabilities", []))

            if success:
                message = f"""
✅ *اكتمل الفحص*

`{scan_id}`

🎯 الهدف: {context.target}
⏱️ المدة: {int(time.time() - context.started_at)}s

📊 النتائج:
"""
                if vuln_count > 0:
                    message += f"⚠️ ثغرات: {vuln_count}\n"
                else:
                    message += f"✅ لا ثغرات مكتشفة\n"

                message += f"\n📈 التقدم: {context.progress:.0f}%\n"
                message += f"\nاستخدم /report {scan_id} لعرض التفاصيل"
            else:
                message = f"""
❌ *فشل الفحص*

`{scan_id}`

🎯 الهدف: {context.target}
⏱️ المدة: {int(time.time() - context.started_at)}s

⚠️ السبب:
{results.get('error', 'خطأ غير معروف')}
"""
            await self.telegram.send_notification(context.user_id, message)

    # ═══════════════════════════════════════════════════════════════════════
    # BYPASS INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════

    async def analyze_block_and_generate_plans(
        self,
        scan_id: str,
        target: str,
        waf_type: str,
        block_response: str,
        attempted_techniques: Optional[List[str]] = None
    ) -> List[BypassPlanFromAI]:
        """
        تحليل الحظر وتوليد خطط بديلة باستخدام DeepSeek

        Args:
            scan_id: معرف الفحص
            target: الهدف
            waf_type: نوع WAF
            block_response: استجابة الحظر
            attempted_techniques: التقنيات التي تم تجربتها

        Returns:
            قائمة بـ 3 خطط بديلة
        """
        if scan_id in self.active_scans:
            context = self.active_scans[scan_id]
            context.state = BrainState.ANALYZING
            context.bypass_attempts += 1

        if not self.deepseek:
            return self._generate_fallback_plans(target, waf_type)

        self.stats["ai_requests"] += 1

        try:
            plans = await self.deepseek.analyze_waf_and_generate_bypass_plans(
                target=target,
                waf_type=waf_type,
                block_response=block_response,
                attempted_techniques=attempted_techniques
            )

            if scan_id in self.active_scans:
                self.active_scans[scan_id].generated_plans = plans
                self.active_scans[scan_id].failed_techniques.extend(
                    attempted_techniques or []
                )

            return plans

        except Exception as e:
            if scan_id in self.active_scans:
                self.active_scans[scan_id].errors.append(f"DeepSeek error: {str(e)}")

            return self._generate_fallback_plans(target, waf_type)

    async def generate_alternative_paths(
        self,
        scan_id: str,
        target: str,
        blocked_path: str,
        block_reason: str,
        available_endpoints: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        توليد مسارات بديلة

        Args:
            scan_id: معرف الفحص
            target: الهدف
            blocked_path: المسار المحظور
            block_reason: سبب الحظر
            available_endpoints: نقاط النهاية المتاحة

        Returns:
            قائمة المسارات البديلة
        """
        if not self.deepseek:
            return self._generate_fallback_paths(target)

        self.stats["ai_requests"] += 1

        try:
            paths = await self.deepseek.generate_alternative_paths(
                target=target,
                current_path=blocked_path,
                block_reason=block_reason,
                available_endpoints=available_endpoints
            )

            return paths

        except Exception:
            return self._generate_fallback_paths(target)

    async def generate_adaptive_fingerprint(
        self,
        scan_id: str,
        target: str,
        current_fingerprint: str,
        waf_type: str
    ) -> Dict[str, Any]:
        """
        توليد بصمة تكيّفية جديدة

        Args:
            scan_id: معرف الفحص
            target: الهدف
            current_fingerprint: البصمة الحالية
            waf_type: نوع WAF

        Returns:
            بيانات البصمة الجديدة
        """
        if not self.deepseek:
            return self._generate_fallback_fingerprint()

        self.stats["ai_requests"] += 1

        # Get failed attempts for this scan
        failed_attempts = []
        if scan_id in self.active_scans:
            failed_attempts = self.active_scans[scan_id].failed_techniques

        try:
            fingerprint = await self.deepseek.generate_adaptive_fingerprint(
                target=target,
                current_fingerprint=current_fingerprint,
                waf_type=waf_type,
                failed_attempts=failed_attempts
            )

            return fingerprint

        except Exception:
            return self._generate_fallback_fingerprint()

    async def analyze_vulnerability(
        self,
        scan_id: str,
        endpoint: str,
        response: str,
        technologies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        تحليل الثغرات المحتملة

        Args:
            scan_id: معرف الفحص
            endpoint: نقطة النهاية
            response: استجابة الخادم
            technologies: التقنيات المكتشفة

        Returns:
            قائمة الثغرات المحتملة
        """
        if not self.deepseek:
            return []

        self.stats["ai_requests"] += 1

        try:
            vulns = await self.deepseek.analyze_vulnerability(
                endpoint=endpoint,
                response=response,
                technologies=technologies
            )

            return vulns

        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════════════════
    # ERROR HANDLING
    # ═══════════════════════════════════════════════════════════════════════

    async def handle_error(
        self,
        scan_id: str,
        error: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        معالجة خطأ وتوليد خطة تعافي

        Args:
            scan_id: معرف الفحص
            error: وصف الخطأ
            context: سياق إضافي
        """
        if scan_id in self.active_scans:
            self.active_scans[scan_id].errors.append(error)
            self.active_scans[scan_id].state = BrainState.ERROR

        # Send error notification
        if self.telegram and self.config.auto_update_telegram:
            message = f"""
⚠️ *خطأ في الفحص*

`{scan_id}`

❌ {error}
"""
            if context:
                message += f"\n📋 السياق:\n"
                for key, value in context.items():
                    message += f"• {key}: {value}\n"

            user_id = self.active_scans[scan_id].user_id if scan_id in self.active_scans else 0
            if user_id:
                await self.telegram.send_notification(user_id, message)

    # ═══════════════════════════════════════════════════════════════════════
    # FALLBACK METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_fallback_plans(
        self,
        target: str,
        waf_type: str
    ) -> List[BypassPlanFromAI]:
        """توليد خطط بديلة افتراضية"""
        return [
            BypassPlanFromAI(
                plan_id="PLAN_A",
                plan_name="Conservative Header Rotation",
                description="تدوير بسيط للـ Headers",
                techniques=["header_rotation", "user_agent_swap"],
                headers_to_modify={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "X-Forwarded-For": "127.0.0.1",
                    "Accept-Language": "en-US,en;q=0.9"
                },
                payload_modifications=None,
                timing_strategy={"delay_ms": 500, "jitter": 100},
                confidence_score=0.6,
                reasoning="تقنية محافظة",
                success_criteria=["status_200", "no_waf_block"]
            ),
            BypassPlanFromAI(
                plan_id="PLAN_B",
                plan_name="Protocol Obfuscation",
                description="تغيير مستوى البروتوكول",
                techniques=["http_downgrade", "header_permutation"],
                headers_to_modify={
                    "HTTP-Version": "HTTP/1.0",
                    "Connection": "keep-alive",
                    "X-Requested-With": "XMLHttpRequest"
                },
                payload_modifications={"double_encoding": True},
                timing_strategy={"delay_ms": 1000, "jitter": 200},
                confidence_score=0.5,
                reasoning="تخفيض HTTP",
                success_criteria=["status_200", "content_length > 100"]
            ),
            BypassPlanFromAI(
                plan_id="PLAN_C",
                plan_name="Aggressive Multi-Vector",
                description="تقنيات متعددة متقدمة",
                techniques=["fragmentation", "timing_manipulation", "encoding_variation"],
                headers_to_modify={
                    "CF-Connecting-IP": "127.0.0.1",
                    "True-Client-IP": "127.0.0.1",
                    "X-Real-IP": "127.0.0.1"
                },
                payload_modifications={"fragment_payload": True},
                timing_strategy={"delay_ms": 2000, "jitter": 500},
                confidence_score=0.4,
                reasoning="محاولة مكثفة",
                success_criteria=["status_200", "no_block_page"]
            )
        ]

    def _generate_fallback_paths(self, target: str) -> List[Dict[str, Any]]:
        """توليد مسارات بديلة افتراضية"""
        return [
            {"path": f"{target}/?p=v", "technique": "query_param", "confidence": 0.7},
            {"path": f"{target}/./path", "technique": "path_traversal", "confidence": 0.5},
            {"path": f"{target}//path", "technique": "double_slash", "confidence": 0.6}
        ]

    def _generate_fallback_fingerprint(self) -> Dict[str, Any]:
        """توليد بصمة افتراضية"""
        return {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "headers_order": ["Host", "User-Agent", "Accept", "Connection"],
            "tls_profile": "chrome_default",
            "timing_pattern": {"delay_ms": 200, "jitter": 50}
        }

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _create_progress_bar(self, progress: float, length: int = 20) -> str:
        """إنشاء شريط تقدم نصي"""
        filled = int(length * progress / 100)
        empty = length - filled

        bar = "█" * filled + "░" * empty
        return f"[{bar}] {progress:.0f}%"

    async def get_scan_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على حالة الفحص"""
        if scan_id not in self.active_scans:
            return None

        context = self.active_scans[scan_id]
        return {
            "scan_id": context.scan_id,
            "target": context.target,
            "scan_type": context.scan_type,
            "state": context.state.value,
            "progress": context.progress,
            "current_phase": context.current_phase,
            "bypass_attempts": context.bypass_attempts,
            "errors": context.errors,
            "results": context.results
        }

    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الدماغ"""
        stats = {
            **self.stats,
            "active_scans": len([
                s for s in self.active_scans.values()
                if s.state == BrainState.SCANNING
            ]),
            "total_scans": len(self.active_scans),
            "state": self.state.value
        }

        if self.deepseek:
            stats["deepseek"] = self.deepseek.get_statistics()

        if self.telegram:
            stats["telegram"] = self.telegram.get_statistics()

        return stats

    async def health_check(self) -> Dict[str, bool]:
        """فحص حالة جميع المكونات"""
        results = {
            "brain": True,
            "deepseek": False,
            "telegram": False
        }

        if self.deepseek:
            results["deepseek"] = await self.deepseek.health_check()

        if self.telegram:
            results["telegram"] = await self.telegram.health_check()

        return results


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_brain(
    deepseek_api_key: Optional[str] = None,
    telegram_bot_token: Optional[str] = None,
    auto_bypass: bool = True,
    auto_update_telegram: bool = True
) -> VIPX1Brain:
    """
    إنشاء وتهيئة الدماغ المركزي

    Args:
        deepseek_api_key: مفتاح DeepSeek API
        telegram_bot_token: مفتاح Telegram Bot
        auto_bypass: تفعيل التجاوز التلقائي
        auto_update_telegram: إرسال تحديثات لـ Telegram

    Returns:
        VIPX1Brain instance
    """
    config = BrainConfig(
        deepseek_api_key=deepseek_api_key or "",
        telegram_bot_token=telegram_bot_token or "",
        auto_bypass=auto_bypass,
        auto_update_telegram=auto_update_telegram
    )

    brain = VIPX1Brain(config=config)
    await brain.initialize(
        deepseek_api_key=deepseek_api_key,
        telegram_bot_token=telegram_bot_token
    )

    return brain
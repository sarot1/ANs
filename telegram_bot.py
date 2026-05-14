"""
R1X Platform - Telegram Bot Interface
واجهة التحكم عبر Telegram Bot
Version: 3.0.0

وظائف هذا الملف:
-接收 أوامر من المستخدم عبر Telegram
- عرض حالة الفحص في الوقت الحقيقي
- إرسال نتائج الفحص
- التحكم بالنظام بالكامل
- أوامر باللغة العربية
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import aiohttp


# ═══════════════════════════════════════════════════════════════════════════════
# BOT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramConfig:
    """إعدادات Telegram Bot"""

    # Bot Token
    BOT_TOKEN: str = "8727732855:AAFaU0_coFVBzeR4D7LarvWop-W1KhszKe8"
    API_URL: str = f"https://api.telegram.org/bot"

    # Polling Settings
    POLL_TIMEOUT: float = 60.0
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 5.0

    # Command Settings
    COMMAND_PREFIX: str = "/"
    ADMIN_IDS: List[int] = []  # Add admin user IDs here

    # Message Settings
    MAX_MESSAGE_LENGTH: int = 4096
    SPLIT_THRESHOLD: int = 3000
    INLINE_KEYBOARD_ROWS: int = 3


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

class CommandType(Enum):
    """أنواع الأوامر"""
    SCAN = "scan"                    # بدء فحص جديد
    STATUS = "status"               # عرض الحالة
    STOP = "stop"                   # إيقاف الفحص
    PAUSE = "pause"                 # إيقاف مؤقت
    RESUME = "resume"               # استئناف الفحص
    HELP = "help"                   # عرض المساعدة
    STATS = "stats"                 # عرض الإحصائيات
    REPORT = "report"               # عرض التقرير
    CANCEL = "cancel"               # إلغاء العملية
    SETTINGS = "settings"           # إعدادات
    AGENTS = "agents"               # عرض الوكلاء
    LOGS = "logs"                   # عرض السجلات


@dataclass
class TelegramCommand:
    """أمر Telegram"""
    command: str
    description_ar: str
    description_en: str
    handler: Callable
    admin_only: bool = False
    requires_args: bool = False
    args_description: Optional[str] = None


@dataclass
class BotUser:
    """مستخدم البوت"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = False
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    active_scan_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanSession:
    """جلسة فحص"""
    scan_id: str
    user_id: int
    target: str
    scan_type: str
    status: str  # running, paused, completed, failed, stopped
    started_at: float
    progress: float = 0.0
    current_phase: str = ""
    results: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

class CommandHandlers:
    """معالجات الأوامر"""

    def __init__(self, bot: 'TelegramBot'):
        self.bot = bot

    async def handle_scan(self, message: Dict[str, Any], args: str) -> str:
        """
        أمر بدء فحص جديد
        /scan https://example.com full_scan
        """
        if not args:
            return self._format_response(
                success=False,
                message="❌ صيغة الأمر غير صحيحة\n\n" +
                        "الصيغة: /scan <الرابط> [نوع الفحص]\n\n" +
                        "أنواع الفحص المتاحة:\n" +
                        "• full_scan - فحص كامل\n" +
                        "• quick_scan - فحص سريع\n" +
                        "• deep_scan - فحص عميق\n" +
                        "• recon - استطلاع فقط\n" +
                        "• vuln_scan - فحص ثغرات فقط\n\n" +
                        "مثال:\n" +
                        "/scan https://example.com full_scan"
            )

        parts = args.split(maxsplit=2)
        target = parts[0] if len(parts) >= 1 else ""
        scan_type = parts[1] if len(parts) >= 2 else "full_scan"

        # Validate URL
        if not target.startswith(("http://", "https://")):
            return self._format_response(
                success=False,
                message="❌ الرابط غير صحيح\n" +
                        "يجب أن يبدأ بـ http:// أو https://"
            )

        # Validate scan type
        valid_types = ["full_scan", "quick_scan", "deep_scan", "recon", "vuln_scan", "enumeration"]
        if scan_type not in valid_types:
            return self._format_response(
                success=False,
                message=f"❌ نوع الفحص '{scan_type}' غير صحيح\n" +
                        f"الأنواع المتاحة: {', '.join(valid_types)}"
            )

        # Create scan session
        user_id = message.get("from", {}).get("id")
        scan_id = hashlib.sha256(f"{target}:{time.time()}".encode()).hexdigest()[:12]

        session = ScanSession(
            scan_id=scan_id,
            user_id=user_id,
            target=target,
            scan_type=scan_type,
            status="running",
            started_at=time.time()
        )

        self.bot.sessions[scan_id] = session

        return self._format_response(
            success=True,
            message=f"🔍 تم بدء الفحص!\n\n" +
                    f"📋 التفاصيل:\n" +
                    f"• الهدف: {target}\n" +
                    f"• نوع الفحص: {scan_type}\n" +
                    f"• معرف الفحص: `{scan_id}`\n\n" +
                    f"⏳ جاري الفحص...\n" +
                    f"استخدم /status {scan_id} لمتابعة التقدم"
        )

    async def handle_status(self, message: Dict[str, Any], args: str) -> str:
        """
        عرض حالة الفحص
        /status <scan_id>
        """
        if not args:
            # Show all active scans for user
            user_id = message.get("from", {}).get("id")
            user_sessions = [
                s for s in self.bot.sessions.values()
                if s.user_id == user_id and s.status in ("running", "paused")
            ]

            if not user_sessions:
                return self._format_response(
                    success=True,
                    message="📭 لا توجد عمليات فحص نشطة\n\n" +
                            "استخدم /scan <الرابط> لبدء فحص جديد"
                )

            response = "📊 عمليات الفحص النشطة:\n\n"
            for session in user_sessions:
                elapsed = int(time.time() - session.started_at)
                response += f"🔹 `{session.scan_id}`\n"
                response += f"   الهدف: {session.target}\n"
                response += f"   التقدم: {session.progress:.0f}%\n"
                response += f"   المرحلة: {session.current_phase}\n"
                response += f"   الوقت: {elapsed}s\n\n"

            return self._format_response(success=True, message=response)

        # Show specific scan status
        scan_id = args.split()[0]
        session = self.bot.sessions.get(scan_id)

        if not session:
            return self._format_response(
                success=False,
                message=f"❌ لم يتم العثور على عملية فحص بالمعرف: `{scan_id}`"
            )

        elapsed = int(time.time() - session.started_at)
        status_emoji = {
            "running": "🟢",
            "paused": "🟡",
            "completed": "✅",
            "failed": "❌",
            "stopped": "⏹️"
        }.get(session.status, "⚪")

        response = f"{status_emoji} حالة الفحص:\n\n"
        response += f"📋 معرف الفحص: `{session.scan_id}`\n"
        response += f"🎯 الهدف: {session.target}\n"
        response += f"📊 نوع الفحص: {session.scan_type}\n"
        response += f"⏱️ الوقت المنقضي: {elapsed}s\n"
        response += f"📈 التقدم: {session.progress:.0f}%\n"
        response += f"🔄 المرحلة: {session.current_phase}\n"
        response += f"📌 الحالة: {session.status}\n\n"

        if session.errors:
            response += f"⚠️ الأخطاء:\n"
            for error in session.errors[-3:]:
                response += f"  • {error}\n"

        if session.results:
            response += f"\n📊 النتائج:\n"
            response += f"  • الثغرات: {len(session.results.get('vulnerabilities', []))}\n"
            response += f"  • نقاط النهاية: {len(session.results.get('endpoints', []))}\n"
            response += f"  • الملفات: {len(session.results.get('files', []))}\n"

        return self._format_response(success=True, message=response)

    async def handle_stop(self, message: Dict[str, Any], args: str) -> str:
        """إيقاف الفحص /stop <scan_id>"""
        if not args:
            return self._format_response(
                success=False,
                message="❌ الصيغة: /stop <معرف الفحص>\n\n" +
                        "استخدم /status لعرض معرفات الفحوصات النشطة"
            )

        scan_id = args.split()[0]
        session = self.bot.sessions.get(scan_id)

        if not session:
            return self._format_response(
                success=False,
                message=f"❌ لم يتم العثور على الفحص: `{scan_id}`"
            )

        if session.status == "completed":
            return self._format_response(
                success=False,
                message="❌ لا يمكن إيقاف فحص مكتمل"
            )

        session.status = "stopped"

        return self._format_response(
            success=True,
            message=f"⏹️ تم إيقاف الفحص: `{scan_id}`\n\n" +
                    "استخدم /report {scan_id} لعرض التقرير"
        )

    async def handle_help(self, message: Dict[str, Any], args: str) -> str:
        """عرض المساعدة /help"""
        help_text = """
🤖 *أوامر VIPX1 Bot*

*أوامر الفحص:*
/scan <الرابط> [نوع] - بدء فحص جديد
/status [معرف] - عرض حالة الفحص
/stop <معرف> - إيقاف الفحص
/report <معرف> - عرض التقرير

*أوامر النظام:*
/agents - عرض الوكلاء المتاحين
/stats - عرض الإحصائيات
/logs [عدد] - عرض آخر السجلات

*أنواع الفحص:*
• full_scan - فحص شامل
• quick_scan - فحص سريع
• deep_scan - فحص عميق
• recon - استطلاع فقط
• vuln_scan - ثغرات فقط
• enumeration - تعداد فقط

*أمثلة:*
/scan https://example.com full_scan
/status abc123
/report abc123

*للمساعدة:* /help
"""
        return self._format_response(success=True, message=help_text)

    async def handle_stats(self, message: Dict[str, Any], args: str) -> str:
        """عرض الإحصائيات /stats"""
        total_scans = len(self.bot.sessions)
        active_scans = len([s for s in self.bot.sessions.values() if s.status == "running"])
        completed_scans = len([s for s in self.bot.sessions.values() if s.status == "completed"])

        response = f"""
📊 *إحصائيات VIPX1*

🔢 *الفحوصات:*
• الإجمالي: {total_scans}
• نشطة: {active_scans}
• مكتملة: {completed_scans}

🤖 *DeepSeek:*
• الطلبات: {self.bot.deepseek_stats.get('requests_total', 0)}
• نجاح: {self.bot.deepseek_stats.get('requests_success', 0)}
• فشل: {self.bot.deepseek_stats.get('requests_failed', 0)}

💾 *التخزين المؤقت:*
•命中率: {self.bot.deepseek_stats.get('cache_hit_rate', 0):.1%}
"""
        return self._format_response(success=True, message=response)

    async def handle_report(self, message: Dict[str, Any], args: str) -> str:
        """عرض التقرير /report <scan_id>"""
        if not args:
            return self._format_response(
                success=False,
                message="❌ الصيغة: /report <معرف الفحص>"
            )

        scan_id = args.split()[0]
        session = self.bot.sessions.get(scan_id)

        if not session:
            return self._format_response(
                success=False,
                message=f"❌ لم يتم العثور على الفحص: `{scan_id}`"
            )

        if not session.results:
            return self._format_response(
                success=False,
                message=f"⏳ الفحص لم يكتمل بعد\n" +
                        f"الحالة: {session.status}\n" +
                        f"التقدم: {session.progress:.0f}%"
            )

        vuln_count = len(session.results.get('vulnerabilities', []))

        response = f"""
📋 *تقرير الفحص:* `{scan_id}`

🎯 *الهدف:* {session.target}
⏱️ *المدة:* {int(time.time() - session.started_at)}s

🔍 *النتائج:*
"""
        if vuln_count > 0:
            response += f"⚠️ ثغرات مكتشفة: {vuln_count}\n"
            for vuln in session.results.get('vulnerabilities', [])[:5]:
                response += f"  • {vuln.get('title', 'Unknown')}\n"
        else:
            response += "✅ لم يتم العثور على ثغرات\n"

        response += f"\n📊 *إحصائيات إضافية:*\n"
        response += f"• نقاط النهاية: {len(session.results.get('endpoints', []))}\n"
        response += f"• الملفات: {len(session.results.get('files', []))}\n"

        return self._format_response(success=True, message=response)

    async def handle_agents(self, message: Dict[str, Any], args: str) -> str:
        """عرض الوكلاء /agents"""
        agents_text = """
🕵️ *الوكلاء المتاحون في VIPX1*

*1. Recon Agent (وكيل الاستطلاع)*
   📡 فحص الأهداف وجمع المعلومات

*2. Scanner Agent (وكيل الفحص)*
   💥 اكتشاف الثغرات الأمنية

*3. Intelligence Agent (وكيل الذكاء)*
   🧠 تحليل الأنماط والتهديدات

*4. DeepSeek Agent (وكيل الذكاء الاصطناعي)*
   🤖 تحليل ذكي وتوليد خطط بديلة

*5. Bypass Agent (وكيل التجاوز)*
   🔓 تجاوز جدران الحماية

*6. Telemetry Agent (وكيل المراقبة)*
   📊 مراقبة الأداء والنظام

*7. Performance Agent (وكيل الأداء)*
   ⚡ تحسين السرعة والكفاءة

*8. Stealth Agent (وكيل التخفي)*
   👻 تقنيات التخفي والمراوغة

*9. Remediation Agent (وكيل الإصلاح)*
   🔧 توليد حلول للثغرات المكتشفة
"""
        return self._format_response(success=True, message=agents_text)

    async def handle_pause(self, message: Dict[str, Any], args: str) -> str:
        """إيقاف مؤقت /pause <scan_id>"""
        if not args:
            return self._format_response(
                success=False,
                message="❌ الصيغة: /pause <معرف الفحص>"
            )

        scan_id = args.split()[0]
        session = self.bot.sessions.get(scan_id)

        if not session:
            return self._format_response(
                success=False,
                message=f"❌ لم يتم العثور على الفحص: `{scan_id}`"
            )

        if session.status != "running":
            return self._format_response(
                success=False,
                message=f"❌ الفحص ليس في حالة نشطة\n" +
                        f"الحالة الحالية: {session.status}"
            )

        session.status = "paused"

        return self._format_response(
            success=True,
            message=f"⏸️ تم إيقاف الفحص مؤقتاً: `{scan_id}`\n\n" +
                    "استخدم /resume {scan_id} للاستئناف"
        )

    async def handle_resume(self, message: Dict[str, Any], args: str) -> str:
        """استئناف الفحص /resume <scan_id>"""
        if not args:
            return self._format_response(
                success=False,
                message="❌ الصيغة: /resume <معرف الفحص>"
            )

        scan_id = args.split()[0]
        session = self.bot.sessions.get(scan_id)

        if not session:
            return self._format_response(
                success=False,
                message=f"❌ لم يتم العثور على الفحص: `{scan_id}`"
            )

        if session.status != "paused":
            return self._format_response(
                success=False,
                message=f"❌ الفحص ليس في حالة إيقاف مؤقت\n" +
                        f"الحالة الحالية: {session.status}"
            )

        session.status = "running"

        return self._format_response(
            success=True,
            message=f"▶️ تم استئناف الفحص: `{scan_id}`\n\n" +
                    "استخدم /status {scan_id} لمتابعة التقدم"
        )

    async def handle_cancel(self, message: Dict[str, Any], args: str) -> str:
        """إلغاء جميع العمليات /cancel"""
        user_id = message.get("from", {}).get("id")
        user_sessions = [
            s for s in self.bot.sessions.values()
            if s.user_id == user_id
        ]

        count = 0
        for session in user_sessions:
            if session.status in ("running", "paused"):
                session.status = "stopped"
                count += 1

        return self._format_response(
            success=True,
            message=f"🛑 تم إلغاء {count} عملية فحص"
        )

    async def handle_logs(self, message: Dict[str, Any], args: str) -> str:
        """عرض السجلات /logs [عدد]"""
        lines = int(args.split()[0]) if args else 10
        lines = min(lines, 50)  # Max 50 lines

        # Get recent logs (simulated)
        logs = self.bot.log_buffer[-lines:] if self.bot.log_buffer else []

        if not logs:
            return self._format_response(
                success=True,
                message="📋 لا توجد سجلات حديثة"
            )

        response = "📋 *آخر السجلات:*\n\n"
        for log in logs:
            timestamp = datetime.fromtimestamp(log.get("timestamp", 0)).strftime("%H:%M:%S")
            level = log.get("level", "INFO")
            message_text = log.get("message", "")

            emoji = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️", "DEBUG": "🔍"}.get(level, "•")
            response += f"{emoji} `[{timestamp}]` {message_text}\n"

        return self._format_response(success=True, message=response)

    def _format_response(self, success: bool, message: str) -> str:
        """تنسيق الاستجابة"""
        return message


# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramBot:
    """
    🤖 Telegram Bot - واجهة التحكم

    الميزات:
    - أوامر باللغة العربية
    - تحديثات في الوقت الحقيقي
    - جلسات فحص متعددة
    - مرونة في التحكم
    """

    def __init__(
        self,
        config: Optional[TelegramConfig] = None,
        deepseek_client: Optional[Any] = None
    ):
        self.config = config or TelegramConfig()
        self.deepseek_client = deepseek_client

        self._session: Optional[aiohttp.ClientSession] = None
        self._running: bool = False
        self._offset: int = 0

        # User management
        self.users: Dict[int, BotUser] = {}
        self.sessions: Dict[str, ScanSession] = {}

        # Command handlers
        self.handlers = CommandHandlers(self)

        # Logging
        self.log_buffer: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            "messages_received": 0,
            "commands_executed": 0,
            "errors": 0
        }

        # DeepSeek stats (to be updated from main system)
        self.deepseek_stats: Dict[str, Any] = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "cache_hit_rate": 0
        }

        # Command mapping
        self.commands: Dict[str, Callable] = {
            "scan": self.handlers.handle_scan,
            "status": self.handlers.handle_status,
            "stop": self.handlers.handle_stop,
            "pause": self.handlers.handle_pause,
            "resume": self.handlers.handle_resume,
            "help": self.handlers.handle_help,
            "stats": self.handlers.handle_stats,
            "report": self.handlers.handle_report,
            "cancel": self.handlers.handle_cancel,
            "agents": self.handlers.handle_agents,
            "logs": self.handlers.handle_logs
        }

    async def __aenter__(self):
        """Initialize bot"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup bot"""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if self._session:
            return

        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self) -> None:
        """Cleanup HTTP session"""
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None

    def _log(self, level: str, message: str) -> None:
        """Add to log buffer"""
        self.log_buffer.append({
            "timestamp": time.time(),
            "level": level,
            "message": message
        })
        # Keep only last 100 logs
        if len(self.log_buffer) > 100:
            self.log_buffer = self.log_buffer[-100:]

    # ═══════════════════════════════════════════════════════════════════════
    # TELEGRAM API METHODS
    # ═══════════════════════════════════════════════════════════════════════

    async def _send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """إرسال رسالة عبر Telegram API"""
        url = f"{self.config.API_URL}{self.config.BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)

        try:
            async with self._session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self._log("ERROR", f"Failed to send message: {response.status}")
                    return None

        except Exception as e:
            self._log("ERROR", f"Failed to send message: {str(e)}")
            return None

    async def _get_updates(self, offset: int) -> List[Dict[str, Any]]:
        """جلب التحديثات من Telegram API"""
        url = f"{self.config.API_URL}{self.config.BOT_TOKEN}/getUpdates"

        params = {
            "offset": offset,
            "timeout": int(self.config.POLL_TIMEOUT)
        }

        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        return data.get("result", [])
                    return []
                return []

        except Exception as e:
            self._log("ERROR", f"Failed to get updates: {str(e)}")
            return []

    async def _answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None
    ) -> bool:
        """الرد على callback query"""
        url = f"{self.config.API_URL}{self.config.BOT_TOKEN}/answerCallbackQuery"

        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text

        try:
            async with self._session.post(url, json=payload) as response:
                return response.status == 200
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════
    # MAIN POLLING LOOP
    # ═══════════════════════════════════════════════════════════════════════

    async def start(self) -> None:
        """بدء البوت - حلقة الاستطلاع الرئيسية"""
        self._running = True
        self._log("INFO", "Telegram Bot started")

        # Send startup message (if you have an admin chat_id)
        # await self._send_message(ADMIN_CHAT_ID, "🤖 VIPX1 Bot is now online!")

        while self._running:
            try:
                updates = await self._get_updates(self._offset)

                for update in updates:
                    await self._process_update(update)
                    self._offset = update.get("update_id", 0) + 1

                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.5)

            except Exception as e:
                self._log("ERROR", f"Polling error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry

    async def _process_update(self, update: Dict[str, Any]) -> None:
        """معالجة تحديث واحد من Telegram"""
        self.stats["messages_received"] += 1

        # Handle callback query
        if "callback_query" in update:
            await self._handle_callback_query(update["callback_query"])
            return

        # Handle message
        if "message" in update:
            await self._handle_message(update["message"])
            return

        # Handle edited message
        if "edited_message" in update:
            await self._handle_message(update["edited_message"])

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """معالجة رسالة من المستخدم"""
        # Extract message info
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")

        # Update user
        if user_id not in self.users:
            self.users[user_id] = BotUser(
                user_id=user_id,
                username=message.get("from", {}).get("username"),
                first_name=message.get("from", {}).get("first_name"),
                last_name=message.get("from", {}).get("last_name")
            )

        self.users[user_id].last_activity = time.time()

        # Parse command
        if not text.startswith("/"):
            # Not a command - respond with help
            response = "👋 مرحباً!\n\n" + \
                      "استخدم /help لعرض قائمة الأوامر المتاحة"
            await self._send_message(chat_id, response)
            return

        # Parse command and args
        parts = text[1:].split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Execute command
        self._log("INFO", f"Executing command: {command} with args: {args}")

        if command in self.commands:
            try:
                handler = self.commands[command]
                response = await handler(message, args)
                await self._send_message(chat_id, response)
                self.stats["commands_executed"] += 1

            except Exception as e:
                self._log("ERROR", f"Command execution failed: {str(e)}")
                error_response = f"❌ حدث خطأ أثناء تنفيذ الأمر\n\n{str(e)}"
                await self._send_message(chat_id, error_response)
                self.stats["errors"] += 1
        else:
            response = f"❌ أمر غير معروف: /{command}\n\n" + \
                      "استخدم /help لعرض قائمة الأوامر"
            await self._send_message(chat_id, response)

    async def _handle_callback_query(self, callback: Dict[str, Any]) -> None:
        """معالجة callback query من الأزرار inline"""
        query_id = callback.get("id")
        data = callback.get("data")

        # Parse callback data
        parts = data.split(":")
        action = parts[0]
        params = parts[1:] if len(parts) > 1 else []

        if action == "view_report":
            scan_id = params[0] if params else None
            if scan_id:
                session = self.sessions.get(scan_id)
                if session and session.results:
                    response = f"📋 تقرير الفحص:\n\n"
                    response += f"الثغرات: {len(session.results.get('vulnerabilities', []))}"
                    await self._answer_callback_query(query_id, "تم عرض التقرير")
                else:
                    await self._answer_callback_query(query_id, "الفحص لم يكتمل بعد")

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def update_deepseek_stats(self, stats: Dict[str, Any]) -> None:
        """تحديث إحصائيات DeepSeek"""
        self.deepseek_stats = stats

    async def send_notification(
        self,
        user_id: int,
        message: str,
        priority: str = "normal"
    ) -> bool:
        """
        إرسال إشعار للمستخدم

        Args:
            user_id: معرف المستخدم
            message: نص الرسالة
            priority: مستوى الأولوية (normal, high, urgent)
        """
        return await self._send_message(user_id, message) is not None

    async def broadcast(
        self,
        message: str,
        user_ids: Optional[List[int]] = None
    ) -> int:
        """
        إرسال رسالة لجميع المستخدمين أو مستخدمين محددين

        Args:
            message: نص الرسالة
            user_ids: قائمة معرفات المستخدمين (اختياري)

        Returns:
            عدد الرسائل المرسلة بنجاح
        """
        targets = user_ids or list(self.users.keys())
        sent_count = 0

        for uid in targets:
            result = await self._send_message(uid, message)
            if result:
                sent_count += 1

        return sent_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get bot statistics"""
        return {
            **self.stats,
            "active_users": len(self.users),
            "active_scans": len([s for s in self.sessions.values() if s.status == "running"]),
            "total_sessions": len(self.sessions),
            "deepseek_stats": self.deepseek_stats
        }

    async def stop(self) -> None:
        """إيقاف البوت"""
        self._running = False
        self._log("INFO", "Telegram Bot stopped")

    async def health_check(self) -> bool:
        """Check if bot is working"""
        try:
            url = f"{self.config.API_URL}{self.config.BOT_TOKEN}/getMe"
            async with self._session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("ok", False)
            return False
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

async def create_telegram_bot(
    bot_token: Optional[str] = None,
    deepseek_client: Optional[Any] = None
) -> TelegramBot:
    """إنشاء وتهيئة Telegram Bot"""
    config = TelegramConfig()
    if bot_token:
        config.BOT_TOKEN = bot_token

    bot = TelegramBot(config=config, deepseek_client=deepseek_client)
    await bot.initialize()

    return bot
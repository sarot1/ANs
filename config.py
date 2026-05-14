"""
R1X Platform - Configuration Module
إعدادات API Keys و Environment Variables
Version: 3.0.0
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class APIKeys:
    """مفاتيح API المتاحة"""

    # DeepSeek API
    deepseek_api_key: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", "")
    )

    # Telegram Bot
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )

    # Optional: Additional API keys
    virustotal_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("VIRUSTOTAL_API_KEY", "")
    )
    shodan_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("SHODAN_API_KEY", "")
    )


@dataclass
class AppConfig:
    """إعدادات التطبيق"""

    # Application
    app_name: str = "VIPX1"
    app_version: str = "3.0.0"
    debug: bool = False

    # DeepSeek Settings
    deepseek_model: str = "deepseek-coder"
    deepseek_max_tokens: int = 2048
    deepseek_temperature: float = 0.7

    # Telegram Settings
    telegram_admin_ids: List[int] = field(default_factory=list)

    # Bypass Engine
    max_bypass_attempts: int = 9
    auto_bypass: bool = True

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None


class Config:
    """إعدادات النظام الرئيسية"""

    def __init__(self):
        self.api_keys = APIKeys()
        self.app = AppConfig()

    def get_deepseek_key(self) -> Optional[str]:
        """الحصول على مفتاح DeepSeek"""
        return self.api_keys.deepseek_api_key or None

    def get_telegram_token(self) -> Optional[str]:
        """الحصول على مفتاح Telegram"""
        return self.api_keys.telegram_bot_token or None

    def is_deepseek_configured(self) -> bool:
        """فحص إذا كان DeepSeek مكون"""
        return bool(self.api_keys.deepseek_api_key)

    def is_telegram_configured(self) -> bool:
        """فحص إذا كان Telegram مكون"""
        return bool(self.api_keys.telegram_bot_token)

    def load_from_env(self) -> None:
        """تحميل الإعدادات من Environment Variables"""
        # DeepSeek
        if os.getenv("DEEPSEEK_API_KEY"):
            self.api_keys.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

        # Telegram
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.api_keys.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        # DeepSeek Settings
        if os.getenv("DEEPSEEK_MODEL"):
            self.app.deepseek_model = os.getenv("DEEPSEEK_MODEL")

        if os.getenv("DEEPSEEK_MAX_TOKENS"):
            self.app.deepseek_max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS"))

        # Telegram Admin IDs
        admin_ids = os.getenv("TELEGRAM_ADMIN_IDS", "")
        if admin_ids:
            self.app.telegram_admin_ids = [
                int(x.strip()) for x in admin_ids.split(",") if x.strip()
            ]

        # Bypass Settings
        if os.getenv("MAX_BYPASS_ATTEMPTS"):
            self.app.max_bypass_attempts = int(os.getenv("MAX_BYPASS_ATTEMPTS"))

        # Debug
        if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
            self.app.debug = True

    def validate(self) -> List[str]:
        """التحقق من صحة الإعدادات"""
        errors = []

        if not self.is_deepseek_configured():
            errors.append("DEEPSEEK_API_KEY not set")

        if not self.is_telegram_configured():
            errors.append("TELEGRAM_BOT_TOKEN not set")

        return errors

    def summary(self) -> str:
        """ملخص الإعدادات"""
        lines = [
            "=" * 50,
            "VIPX1 Configuration Summary",
            "=" * 50,
            "",
            f"App Name: {self.app.app_name}",
            f"Version: {self.app.app_version}",
            "",
            "API Keys:",
            f"  DeepSeek: {'✓ Configured' if self.is_deepseek_configured() else '✗ Not Set'}",
            f"  Telegram: {'✓ Configured' if self.is_telegram_configured() else '✗ Not Set'}",
            "",
            "Settings:",
            f"  Max Bypass Attempts: {self.app.max_bypass_attempts}",
            f"  Auto Bypass: {self.app.auto_bypass}",
            f"  DeepSeek Model: {self.app.deepseek_model}",
            f"  Debug Mode: {self.app.debug}",
            "",
            "=" * 50
        ]
        return "\n".join(lines)


# Global config instance
config = Config()
config.load_from_env()
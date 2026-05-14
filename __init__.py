"""
R1X Platform - Autonomous Cyber Intelligence Platform
Version: 2.0.0

A unified platform combining MaxHermes and SAKK Network Auditor
for professional vulnerability scanning and security assessment.
"""

from core.constants import VERSION, PLATFORM_NAME, PLATFORM_FULL_NAME

__version__ = VERSION
__name__ = PLATFORM_NAME
__full_name__ = PLATFORM_FULL_NAME

__all__ = [
    "__version__",
    "__name__",
    "__full_name__",
    "VERSION",
    "PLATFORM_NAME",
    "PLATFORM_FULL_NAME"
]
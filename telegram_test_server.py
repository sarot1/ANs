"""
VIPX1 Telegram Bot - Test Server
خادم اختبار البوت Telegram
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    print("="*60)
    print("🤖 VIPX1 Telegram Bot - Test Server")
    print("="*60)
    
    # Check API keys
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    print("\n📋 Configuration Check:")
    print(f"   DeepSeek API: {'✓ Configured' if deepseek_key else '✗ Not Set'}")
    print(f"   Telegram Token: {'✓ Configured' if telegram_token else '✗ Not Set'}")
    
    if not telegram_token:
        print("\n❌ Telegram bot token is required!")
        print("   Get one from: https://t.me/BotFather")
        return
    
    # Import and run bot
    print("\n🔄 Starting Telegram Bot...")
    
    from api.telegram_bot import create_telegram_bot
    from api.deepseek_client import DeepSeekClient
    
    # Initialize components
    deepseek = None
    if deepseek_key:
        print("   🤖 DeepSeek AI: Initializing...")
        from api.deepseek_client import DeepSeekConfig
        config = DeepSeekConfig()
        config.API_KEY = deepseek_key
        deepseek = DeepSeekClient(config=config)
        await deepseek.initialize()
        print("   ✅ DeepSeek AI: Ready!")
    
    bot = await create_telegram_bot(
        bot_token=telegram_token,
        deepseek_client=deepseek
    )
    
    print("\n" + "="*60)
    print("✅ Bot is running!")
    print("="*60)
    print("\n📱 Telegram Commands:")
    print("   /scan <url> - Start scan")
    print("   /status    - Show status")
    print("   /help      - Show help")
    print("   /stop      - Stop scan")
    print("\n⚠️  Press Ctrl+C to stop")
    print("="*60)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if bot:
            await bot.cleanup()
        if deepseek:
            await deepseek.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

#!/bin/bash
# VIPX1 - Railway Deployment Script
# Author: VIPX1 Team

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🛡️ VIPX1 - نظام التدقيق الأمني الذكي              ║"
echo "║        Autonomous Cyber Intelligence Platform          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Detect server environment
if [ -n "$RAILWAY_STATIC_URL" ] || [ -n "$RAILWAY_PROJECT_ID" ]; then
    echo "🖥️  Railway Environment Detected"
    SERVER_MODE=true
else
    echo "💻 Local Environment Detected"
    SERVER_MODE=false
fi

# Install Python dependencies (always on server, optional locally)
echo ""
echo "📦 Installing Python dependencies..."
pip install --quiet aiohttp python-dotenv beautifulsoup4 lxml || pip install aiohttp python-dotenv beautifulsoup4 lxml
echo "✅ Python dependencies installed"

# Detect and install system tools based on package manager
install_system_tools() {
    echo ""
    echo "🔧 Installing system tools for reconnaissance..."

    # Try apt (Debian/Ubuntu)
    if command -v apt-get &> /dev/null; then
        echo "📦 Detected: apt-based system"
        apt-get update -qq 2>/dev/null
        apt-get install -y -qq curl wget dnsutils nmap 2>/dev/null || true

    # Try yum (RHEL/CentOS)
    elif command -v yum &> /dev/null; then
        echo "📦 Detected: yum-based system"
        yum install -y -q curl wget bind-utils nmap 2>/dev/null || true

    # Try apk (Alpine)
    elif command -v apk &> /dev/null; then
        echo "📦 Detected: Alpine system"
        apk add --quiet curl wget bind-tools nmap 2>/dev/null || true

    # Try pacman (Arch)
    elif command -v pacman &> /dev/null; then
        echo "📦 Detected: Arch system"
        pacman -Sy --noconfirm curl wget bind-tools nmap 2>/dev/null || true

    else
        echo "⚠️  Unknown package manager - skipping system tools"
    fi

    # Verify tools installed
    echo ""
    echo "✅ System tools status:"
    command -v curl &> /dev/null && echo "  ✓ curl" || echo "  ✗ curl"
    command -v wget &> /dev/null && echo "  ✓ wget" || echo "  ✗ wget"
    command -v dig &> /dev/null && echo "  ✓ dnsutils (dig)" || echo "  ✗ dnsutils"
    command -v nmap &> /dev/null && echo "  ✓ nmap" || echo "  ✗ nmap"
}

# Load environment from .env file
if [ -f .env ]; then
    echo ""
    echo "📁 Loading environment variables from .env..."
    set -a
    source .env
    set +a
    echo "✅ Environment loaded"
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

echo "🐍 Python version: $(python3 --version)"

# Install system tools on server
if [ "$SERVER_MODE" = true ]; then
    install_system_tools
fi

# Parse command (default: bot for server, help for local)
COMMAND=${1:-bot}

echo ""
echo "🎯 Executing: $COMMAND"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

case $COMMAND in
    scan)
        echo "🔍 Starting vulnerability scan..."
        python3 main.py scan "${@:2}"
        ;;
    bot)
        echo "🤖 Starting Telegram Bot (24/7 mode)..."
        echo "💡 Bot will auto-restart if stopped"
        while true; do
            python3 telegram_test_server.py
            echo "⚠️ Bot stopped - restarting in 5 seconds..."
            sleep 5
        done
        ;;
    web)
        echo "🌐 Starting Web Control Panel..."
        echo "💡 Access at: http://localhost:8080"
        python3 web_control_panel.py
        ;;
    status)
        echo "📊 System Status Report"
        python3 main.py status
        ;;
    agents)
        echo "🕵️  Available Agents"
        python3 main.py agents
        ;;
    install)
        echo "📦 Full Installation Mode..."
        pip install --quiet aiohttp python-dotenv beautifulsoup4 lxml
        install_system_tools
        echo "✅ Installation complete!"
        ;;
    *)
        echo "📖 Usage: ./run.sh <command> [options]"
        echo ""
        echo "Available Commands:"
        echo "  scan <url>        - Start vulnerability scan"
        echo "  bot               - Start Telegram Bot (24/7)"
        echo "  web               - Start Web Control Panel"
        echo "  status            - Show system status"
        echo "  agents            - List available agents"
        echo "  install           - Install all dependencies"
        echo ""
        echo "Examples:"
        echo "  ./run.sh scan https://example.com"
        echo "  ./run.sh bot"
        echo "  ./run.sh web"
        ;;
esac
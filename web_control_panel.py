"""
VIPX1 - Modern Web Control Panel
Beautiful Dashboard for Cyber Intelligence Operations
Author: VIPX1 Team
"""

import asyncio
import os
from datetime import datetime
from aiohttp import web
import json

# ══════════════════════════════════════════════════════════════════════════════
# MODERN HTML TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ VIPX1 - لوحة التحكم</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6C63FF;
            --primary-dark: #5A52D5;
            --secondary: #00D9FF;
            --accent: #FF6B6B;
            --success: #00C853;
            --warning: #FFB300;
            --danger: #FF1744;
            --bg-dark: #0D1117;
            --bg-card: #161B22;
            --bg-input: #21262D;
            --text-primary: #FFFFFF;
            --text-secondary: #8B949E;
            --border: #30363D;
            --gradient: linear-gradient(135deg, var(--primary), var(--secondary));
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Tajawal', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(108, 99, 255, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(0, 217, 255, 0.1) 0%, transparent 50%),
                var(--bg-dark);
        }

        /* Header */
        .header {
            background: rgba(22, 27, 34, 0.98);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo-icon {
            width: 50px;
            height: 50px;
            background: var(--gradient);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 10px 30px rgba(108, 99, 255, 0.4);
            animation: glow 2s ease-in-out infinite;
        }

        @keyframes glow {
            0%, 100% { box-shadow: 0 10px 30px rgba(108, 99, 255, 0.4); }
            50% { box-shadow: 0 10px 50px rgba(108, 99, 255, 0.6); }
        }

        .logo-text h1 {
            font-size: 28px;
            font-weight: 900;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-text span {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            background: var(--bg-card);
            border-radius: 50px;
            border: 1px solid var(--border);
        }

        .status-dot {
            width: 12px;
            height: 12px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }

        /* Main Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }

        /* Welcome */
        .welcome {
            text-align: center;
            margin-bottom: 50px;
        }

        .welcome h2 {
            font-size: 36px;
            margin-bottom: 10px;
        }

        .welcome p {
            color: var(--text-secondary);
            font-size: 18px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient);
        }

        .stat-icon {
            font-size: 40px;
            margin-bottom: 15px;
        }

        .stat-value {
            font-size: 42px;
            font-weight: 900;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 14px;
            margin-top: 5px;
        }

        /* Grid Layout */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }

        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: var(--primary);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
        }

        .card-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
        }

        .icon-purple { background: rgba(108, 99, 255, 0.2); }
        .icon-blue { background: rgba(0, 217, 255, 0.2); }
        .icon-green { background: rgba(0, 200, 83, 0.2); }
        .icon-red { background: rgba(255, 23, 68, 0.2); }
        .icon-orange { background: rgba(255, 179, 0, 0.2); }

        .card-title {
            font-size: 20px;
            font-weight: 700;
        }

        .card-subtitle {
            font-size: 14px;
            color: var(--text-secondary);
        }

        /* Scan Form */
        .scan-form {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 40px;
        }

        .scan-form h3 {
            font-size: 24px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 10px;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .form-input {
            width: 100%;
            padding: 18px 20px;
            background: var(--bg-input);
            border: 2px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 16px;
            font-family: 'Tajawal', sans-serif;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 30px rgba(108, 99, 255, 0.3);
        }

        .form-select {
            width: 100%;
            padding: 18px 20px;
            background: var(--bg-input);
            border: 2px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 16px;
            font-family: 'Tajawal', sans-serif;
            cursor: pointer;
        }

        .btn {
            padding: 18px 40px;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 700;
            font-family: 'Tajawal', sans-serif;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .btn-primary {
            background: var(--gradient);
            color: white;
            box-shadow: 0 10px 30px rgba(108, 99, 255, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(108, 99, 255, 0.5);
        }

        .btn-secondary {
            background: var(--bg-input);
            color: var(--text-primary);
            border: 2px solid var(--border);
        }

        .btn-secondary:hover {
            border-color: var(--primary);
            background: rgba(108, 99, 255, 0.1);
        }

        /* Console */
        .console {
            background: #000;
            border-radius: 20px;
            padding: 30px;
            font-family: 'Courier New', monospace;
            margin-bottom: 40px;
            border: 1px solid var(--border);
        }

        .console-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
        }

        .console-title {
            color: var(--secondary);
            font-size: 16px;
        }

        .console-content {
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.8;
        }

        .console-line {
            margin-bottom: 8px;
        }

        .console-line.error { color: var(--danger); }
        .console-line.success { color: var(--success); }
        .console-line.warning { color: var(--warning); }
        .console-line.info { color: var(--secondary); }

        /* Commands Grid */
        .commands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }

        .command-card {
            background: var(--bg-input);
            border-radius: 15px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid var(--border);
        }

        .command-card:hover {
            background: rgba(108, 99, 255, 0.1);
            border-color: var(--primary);
            transform: scale(1.02);
        }

        .command-icon {
            font-size: 30px;
            margin-bottom: 10px;
        }

        .command-name {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .command-desc {
            color: var(--text-secondary);
            font-size: 14px;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            margin-top: 50px;
        }

        /* Loading */
        .loading {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(13, 17, 23, 0.95);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }

        .loading.active {
            display: flex;
        }

        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading-text {
            margin-top: 20px;
            font-size: 20px;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .header {
                padding: 15px 20px;
                flex-direction: column;
                gap: 15px;
            }
            .container {
                padding: 20px;
            }
        }

        /* Progress Bar */
        .progress-container {
            width: 100%;
            height: 8px;
            background: var(--bg-input);
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }

        .progress-bar {
            height: 100%;
            background: var(--gradient);
            width: 0%;
            transition: width 0.5s ease;
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>

    <!-- Loading Overlay -->
    <div class="loading" id="loading">
        <div class="spinner"></div>
        <div class="loading-text">جاري التشغيل...</div>
    </div>

    <!-- Header -->
    <header class="header">
        <div class="logo">
            <div class="logo-icon">🛡️</div>
            <div class="logo-text">
                <h1>VIPX1</h1>
                <span>منصة الاستخبارات السيبرانية</span>
            </div>
        </div>
        <div class="status-badge">
            <div class="status-dot"></div>
            <span>متصل</span>
        </div>
    </header>

    <!-- Main Container -->
    <div class="container">
        <!-- Welcome -->
        <div class="welcome">
            <h2>مرحباً بك في لوحة تحكم VIPX1</h2>
            <p>إدارة عمليات الاستخبارات السيبرانية بسهولة وأمان</p>
        </div>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🔍</div>
                <div class="stat-value" id="total-scans">0</div>
                <div class="stat-label">إجمالي الفحوصات</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-value" id="success-scans">0</div>
                <div class="stat-label">فحوصات ناجحة</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚠️</div>
                <div class="stat-value" id="blocked-scans">0</div>
                <div class="stat-label">محاولات محظورة</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🤖</div>
                <div class="stat-value" id="ai-plans">0</div>
                <div class="stat-label">خطط AI</div>
            </div>
        </div>

        <!-- Main Grid -->
        <div class="grid">
            <!-- System Status -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon icon-purple">💻</div>
                    <div>
                        <div class="card-title">حالة النظام</div>
                        <div class="card-subtitle">معلومات الخادم</div>
                    </div>
                </div>
                <div id="system-status">
                    <p>⏳ جاري تحميل معلومات النظام...</p>
                </div>
            </div>

            <!-- API Status -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon icon-blue">🔗</div>
                    <div>
                        <div class="card-title">حالة API</div>
                        <div class="card-subtitle">مفاتيح الاتصال</div>
                    </div>
                </div>
                <div id="api-status">
                    <p>⏳ جاري فحص حالة APIs...</p>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon icon-green">⚡</div>
                    <div>
                        <div class="card-title">إجراءات سريعة</div>
                        <div class="card-subtitle">أوامر التشغيل</div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <button class="btn btn-primary" onclick="runCommand('status')">
                        📊 فحص الحالة
                    </button>
                    <button class="btn btn-secondary" onclick="runCommand('agents')">
                        🕵️ عرض الوكلاء
                    </button>
                </div>
            </div>
        </div>

        <!-- Scan Form -->
        <div class="scan-form">
            <h3>🔍 بدء فحص جديد</h3>
            <form id="scan-form" onsubmit="startScan(event)">
                <div class="form-group">
                    <label>الرابط المستهدف</label>
                    <input type="url" class="form-input" id="target-url"
                           placeholder="https://example.com" required>
                </div>
                <div class="form-group">
                    <label>نوع الفحص</label>
                    <select class="form-select" id="scan-type">
                        <option value="quick">فحص سريع ⚡</option>
                        <option value="full">فحص كامل 🎯</option>
                        <option value="deep">فحص عميق 🔬</option>
                        <option value="stealth">فحص مخفي 👻</option>
                    </select>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" id="progress-bar"></div>
                </div>
                <div style="display: flex; gap: 15px;">
                    <button type="submit" class="btn btn-primary">
                        🚀 بدء الفحص
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="clearForm()">
                        🗑️ مسح
                    </button>
                </div>
            </form>
        </div>

        <!-- Console Output -->
        <div class="console">
            <div class="console-header">
                <span class="console-title">📟 Console Output</span>
                <button class="btn btn-secondary" onclick="clearConsole()" style="padding: 8px 20px; font-size: 14px;">
                    مسح
                </button>
            </div>
            <div class="console-content" id="console-output">
                <div class="console-line info">[00:00:00] 🎉 لوحة VIPX1 جاهزة!</div>
                <div class="console-line info">[00:00:00] 📡 انتظار الأوامر...</div>
            </div>
        </div>

        <!-- Commands -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon icon-orange">🎮</div>
                <div>
                    <div class="card-title">الأوامر المتاحة</div>
                    <div class="card-subtitle">اضغط على الأمر لتنفيذه</div>
                </div>
            </div>
            <div class="commands-grid">
                <div class="command-card" onclick="runCommand('status')">
                    <div class="command-icon">📊</div>
                    <div class="command-name">/status</div>
                    <div class="command-desc">عرض حالة النظام</div>
                </div>
                <div class="command-card" onclick="runCommand('stop')">
                    <div class="command-icon">⏹️</div>
                    <div class="command-name">/stop</div>
                    <div class="command-desc">إيقاف الفحص الحالي</div>
                </div>
                <div class="command-card" onclick="runCommand('pause')">
                    <div class="command-icon">⏸️</div>
                    <div class="command-name">/pause</div>
                    <div class="command-desc">إيقاف مؤقت</div>
                </div>
                <div class="command-card" onclick="runCommand('resume')">
                    <div class="command-icon">▶️</div>
                    <div class="command-name">/resume</div>
                    <div class="command-desc">استئناف الفحص</div>
                </div>
                <div class="command-card" onclick="runCommand('report')">
                    <div class="command-icon">📋</div>
                    <div class="command-name">/report</div>
                    <div class="command-desc">عرض التقرير</div>
                </div>
                <div class="command-card" onclick="runCommand('stats')">
                    <div class="command-icon">📈</div>
                    <div class="command-name">/stats</div>
                    <div class="command-desc">عرض الإحصائيات</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <p>🛡️ VIPX1 Platform © 2024 | Autonomous Cyber Intelligence</p>
        <p style="margin-top: 10px; font-size: 12px;">Powered by DeepSeek AI + Telegram Bot</p>
    </footer>

    <script>
        // Update system status
        async function updateSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                document.getElementById('system-status').innerHTML = `
                    <p>🖥️ النظام: ${data.platform}</p>
                    <p>🐍 Python: ${data.python_version}</p>
                    <p>📁 العمل: ${data.working_dir}</p>
                    <p>⏰ الوقت: ${data.time}</p>
                `;

                document.getElementById('api-status').innerHTML = `
                    <p>🤖 DeepSeek: ${data.deepseek_status}</p>
                    <p>📱 Telegram: ${data.telegram_status}</p>
                `;
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }

        // Run command
        async function runCommand(command) {
            showLoading();
            logToConsole('info', `تنفيذ الأمر: ${command}`);

            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });

                const data = await response.json();
                logToConsole('success', data.output || 'تم تنفيذ الأمر بنجاح');

                if (data.stats) {
                    document.getElementById('total-scans').textContent = data.stats.total || 0;
                    document.getElementById('success-scans').textContent = data.stats.success || 0;
                    document.getElementById('blocked-scans').textContent = data.stats.blocked || 0;
                    document.getElementById('ai-plans').textContent = data.stats.ai_plans || 0;
                }
            } catch (error) {
                logToConsole('error', `خطأ: ${error.message}`);
            }

            hideLoading();
        }

        // Start scan
        async function startScan(event) {
            event.preventDefault();
            showLoading();

            const url = document.getElementById('target-url').value;
            const scanType = document.getElementById('scan-type').value;

            logToConsole('info', `🚀 بدء فحص: ${url}`);
            logToConsole('info', `📋 نوع الفحص: ${scanType}`);

            // Animate progress
            let progress = 0;
            const progressBar = document.getElementById('progress-bar');
            const interval = setInterval(() => {
                progress += 5;
                if (progress <= 90) {
                    progressBar.style.width = progress + '%';
                }
            }, 200);

            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, type: scanType })
                });

                const data = await response.json();
                clearInterval(interval);
                progressBar.style.width = '100%';

                logToConsole('success', `✅ ${data.message}`);

                if (data.scan_id) {
                    logToConsole('info', `🔖 معرف الفحص: ${data.scan_id}`);
                }

                // Update stats
                const statsResponse = await fetch('/api/status');
                const statsData = await statsResponse.json();
                document.getElementById('total-scans').textContent = statsData.total_scans || 0;
                document.getElementById('success-scans').textContent = statsData.success_scans || 0;

                setTimeout(() => {
                    progressBar.style.width = '0%';
                }, 1000);

            } catch (error) {
                clearInterval(interval);
                logToConsole('error', `خطأ: ${error.message}`);
                progressBar.style.width = '0%';
            }

            hideLoading();
        }

        // Console functions
        function logToConsole(type, message) {
            const consoleEl = document.getElementById('console-output');
            const time = new Date().toLocaleTimeString('ar-SA');
            const line = document.createElement('div');
            line.className = `console-line ${type}`;
            line.textContent = `[${time}] ${message}`;
            consoleEl.appendChild(line);
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }

        function clearConsole() {
            document.getElementById('console-output').innerHTML = `
                <div class="console-line info">[${new Date().toLocaleTimeString('ar-SA')}] 🗑️ تم مسح Console</div>
            `;
        }

        // Form functions
        function clearForm() {
            document.getElementById('scan-form').reset();
            document.getElementById('progress-bar').style.width = '0%';
            logToConsole('info', '🗑️ تم مسح النموذج');
        }

        // Loading functions
        function showLoading() {
            document.getElementById('loading').classList.add('active');
        }

        function hideLoading() {
            setTimeout(() => {
                document.getElementById('loading').classList.remove('active');
            }, 500);
        }

        // Initial load
        document.addEventListener('DOMContentLoaded', () => {
            updateSystemStatus();
            setInterval(updateSystemStatus, 30000);
        });
    </script>
</body>
</html>
"""

# ══════════════════════════════════════════════════════════════════════════════
# APPLICATION STATE
# ══════════════════════════════════════════════════════════════════════════════

class AppState:
    def __init__(self):
        self.total_scans = 0
        self.success_scans = 0
        self.blocked_scans = 0
        self.ai_plans = 0
        self.active_scan = None

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

async def handle_index(request):
    """Serve main HTML page"""
    return web.Response(text=HTML_TEMPLATE, content_type='text/html')

async def handle_api_status(request):
    """Get system status"""
    state = request.app['state']

    deepseek_key = os.getenv('DEEPSEEK_API_KEY', '')
    telegram_key = os.getenv('TELEGRAM_BOT_TOKEN', '')

    return web.json_response({
        'platform': 'Linux',
        'python_version': '3.x',
        'working_dir': os.getcwd(),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'deepseek_status': '✅ متصل' if deepseek_key else '❌ غير متصل',
        'telegram_status': '✅ متصل' if telegram_key else '❌ غير متصل',
        'total_scans': state.total_scans,
        'success_scans': state.success_scans,
        'blocked_scans': state.blocked_scans,
        'ai_plans': state.ai_plans
    })

async def handle_api_command(request):
    """Execute command"""
    state = request.app['state']
    data = await request.json()
    command = data.get('command', '')

    output = ""

    if command == 'status':
        output = f"""📊 حالة النظام:
━━━━━━━━━━━━━━━
🔍 إجمالي الفحوصات: {state.total_scans}
✅ ناجحة: {state.success_scans}
⚠️ محظورة: {state.blocked_scans}
🤖 خطط AI: {state.ai_plans}
━━━━━━━━━━━━━━━"""

    elif command == 'agents':
        output = """🕵️ الوكلاء المتاحون:
━━━━━━━━━━━━━━━
🔹 Recon Agent - جمع المعلومات
🔹 DNS Agent - تحليل DNS
🔹 Path Agent - اكتشاف المسارات
🔹 Bypass Agent - تجاوز WAF
🔹 AI Brain - التخطيط الذكي
━━━━━━━━━━━━━━━"""

    elif command == 'stats':
        total = state.total_scans or 1
        success_rate = int(state.success_scans / total * 100)
        blocked_rate = int(state.blocked_scans / total * 100)
        output = f"""📈 الإحصائيات:
━━━━━━━━━━━━━━━
🔍 الفحوصات: {state.total_scans}
✅ نسبة النجاح: {success_rate}%
⚠️ نسبة الحظر: {blocked_rate}%
🤖 خطط AI: {state.ai_plans}
━━━━━━━━━━━━━━━"""

    else:
        output = f"✅ تم تنفيذ: {command}"

    return web.json_response({
        'success': True,
        'output': output,
        'stats': {
            'total': state.total_scans,
            'success': state.success_scans,
            'blocked': state.blocked_scans,
            'ai_plans': state.ai_plans
        }
    })

async def handle_api_scan(request):
    """Start new scan"""
    state = request.app['state']
    data = await request.json()

    url = data.get('url', '')
    scan_type = data.get('type', 'quick')

    state.total_scans += 1
    scan_id = f"scan_{state.total_scans}_{datetime.now().strftime('%H%M%S')}"

    return web.json_response({
        'success': True,
        'message': f'تم بدء الفحص بنجاح!',
        'scan_id': scan_id,
        'url': url,
        'type': scan_type
    })

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

async def init_app():
    """Initialize web application"""
    app = web.Application()
    app['state'] = AppState()

    app.router.add_get('/', handle_index)
    app.router.add_get('/index.html', handle_index)
    app.router.add_get('/api/status', handle_api_status)
    app.router.add_post('/api/command', handle_api_command)
    app.router.add_post('/api/scan', handle_api_scan)

    return app

def main():
    """Run the web control panel"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     🛡️ VIPX1 - لوحة التحكم                              ║
    ║        Web Control Panel v2.0                            ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    print("🌐 بدء لوحة التحكم...")
    print("📍 الرابط: http://localhost:8080")
    print("📍 الرابط: http://0.0.0.0:8080")
    print("")

    app = init_app()
    web.run_app(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
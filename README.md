# VIPX1 - Autonomous Cyber Intelligence Platform

🛡️ نظام التدقيق الأمني الذكي المدعوم بالذكاء الاصطناعي

## 🚀 الميزات

- 🤖 **DeepSeek AI Integration** - تحليل ذكي وتوليد خطط بديلة
- 📱 **Telegram Bot** - تحكم بالنظام من أي مكان
- 🔓 **WAF Bypass Engine** - تجاوز جدران الحماية تلقائياً
- 📊 **Real-time Updates** - تحديثات في الوقت الحقيقي
- 🔍 **Reconnaissance** - جمع المعلومات والبيانات
- 💥 **Vulnerability Scanner** - اكتشاف الثغرات الأمنية

## 🌐 النشر على سيرفر مجاني (Railway.app)

### الخطوة 1: ارفع المشروع على GitHub
```bash
cd /workspace/vipx1_project/R1X
git init
git add .
git commit -m "VIPX1 v3.0.0"
git remote add origin https://github.com/YOUR_USERNAME/R1X.git
git push -u origin main
```

### الخطوة 2: أنشئ مشروع على Railway
1. اذهب إلى https://railway.app
2. سجل دخول بحساب GitHub
3. اضغط "New Project" → "Deploy from GitHub"
4. اختر مستودع `R1X`

### الخطوة 3: أضف Environment Variables
في Railway Dashboard → Variables:
```
DEEPSEEK_API_KEY=sk-43fa71eb41674587a7ca28c0392e5cf3
TELEGRAM_BOT_TOKEN=8727732855:AAFaU0_coFVBzeR4D7LarvWop-W1KhszKe8
```

### الخطوة 4: تشغيل البوت
في Railway Dashboard → Settings → Start Command:
```
bash run.sh bot
```

---

## 📋 المتطلبات المحلية

- Python 3.9+
- DeepSeek API Key
- Telegram Bot Token

## 🔐 إعداد مفاتيح API

### الطريقة 1: ملف .env
```bash
cp .env.example .env
# ثم عدّل .env وأضف المفاتيح
```

### الطريقة 2: Environment Variables
```bash
export DEEPSEEK_API_KEY="your_key_here"
export TELEGRAM_BOT_TOKEN="your_token_here"
```

## 🚀 التشغيل المحلي

### تشغيل الفحص:
```bash
python main.py scan https://example.com
```

### تشغيل Telegram Bot:
```bash
python telegram_test_server.py
```

### التشغيل عبر السكربت:
```bash
./run.sh bot      # تشغيل البوت
./run.sh scan https://example.com  # تشغيل فحص
```

## 📱 أوامر Telegram

| الأمر | الوصف |
|-------|-------|
| `/scan <رابط>` | بدء فحص جديد |
| `/status` | عرض حالة الفحص |
| `/stop <معرف>` | إيقاف الفحص |
| `/report <معرف>` | عرض التقرير |
| `/stats` | عرض الإحصائيات |
| `/help` | عرض المساعدة |

## ⚠️ تنبيه أمني

> ⚠️ **هذا المشروع مخصص للاختبار الأمني المصرح به فقط. الاستخدام غير المصرح به مرفوض.**

## 📄 الرخصة

MIT License

## 👨‍💻 المطور

VIPX1 Team
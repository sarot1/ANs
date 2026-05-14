# 🚀 VIPX1 - دليل النشر على Railway.app (سيرفر مجاني)

## الخطوات بالتفصيل:

---

### الخطوة 1: ارفع المشروع على GitHub

من سطر الأوامر في مشروعك:
```bash
cd /workspace/vipx1_project/R1X

# تهيئة Git
git init
git add .
git commit -m "VIPX1 v3.0.0 - DeepSeek AI Integration"

# اضف المستودع الجديد
git remote add origin https://github.com/YOUR_USERNAME/R1X.git

# ارفع الكود
git push -u origin main
```

استبدل `YOUR_USERNAME` باسم مستخدم GitHub الخاص بك.

---

### الخطوة 2: أنشئ حساب Railway.app

1. اذهب إلى https://railway.app
2. سجل دخول بحساب GitHub
3. اضغط "New Project" → "Deploy from GitHub repo"
4. اختر مستودع `R1X`

---

### الخطوة 3: أضف Environment Variables

في Railway Dashboard:
1. اضغط على المشروع
2. اذهب إلى "Variables"
3. أضف:

```
DEEPSEEK_API_KEY=sk-43fa71eb41674587a7ca28c0392e5cf3
TELEGRAM_BOT_TOKEN=8727732855:AAFaU0_coFVBzeR4D7LarvWop-W1KhszKe8
```

---

### الخطوة 4: أضف Nixpacks Build Configuration

يحتوي مشروعك الآن على `railway.json` للتثبيت التلقائي لأدوات Linux.

---

### الخطوة 5: تشغيل البوت

من Railway Dashboard:
1. اذهب إلى "Settings" → "Start Command"
2. ضع:
```
bash run.sh
```

أو يمكنك تشغيل البوت مباشرة:
```
python telegram_test_server.py
```

---

## 🎯 بعد التثبيت

### التحقق من البوت:
أرسل رسالة على Telegram:
```
/start
```

سترى:
```
🛡️ VIPX1 Bot مفعّل!
🔗 API Keys: ✓ DeepSeek ✓ Telegram
⚙️ النوع: production
💡 أرسل /help للمساعدة
```

---

## 📊 مراقبة السجلات

في Railway:
1. اضغط على "Deployments"
2. اختر آخر deployment
3. اضغط "Logs" لمشاهدة السجلات الحية

---

## 🔄 إعادة التشغيل التلقائي

Railway يعيد تشغيل البوت تلقائياً إذا توقف.

---

## 💡 ملاحظات مهمة:

1. **النطاق المجاني**: 500 ساعة شهرياً
2. **البوت يعمل 24/7**: نعم، على الخطة المجانية
3. **SSL/TLS**: مجاني تلقائياً
4. **الدومين**: `your-project.railway.app`

---

هل تحتاج مساعدة إضافية في أي خطوة؟
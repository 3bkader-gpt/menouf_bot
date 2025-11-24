# 📚 دليل تشغيل المشروع - Uploader Bot

## 🚀 الخطوات السريعة

### 1️⃣ تفعيل البيئة الافتراضية (Virtual Environment)

#### على Windows (PowerShell):
```powershell
# تفعيل البيئة الافتراضية
.venv\Scripts\activate

# أو إذا لم تعمل، جرب:
.\.venv\Scripts\Activate.ps1
```

#### على Windows (CMD):
```cmd
.venv\Scripts\activate.bat
```

#### على Linux/Mac:
```bash
source .venv/bin/activate
```

**✅ علامة النجاح:** ستظهر `(bot)` في بداية السطر في الـ Terminal.

---

### 2️⃣ تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

**ملاحظة:** إذا كانت البيئة الافتراضية مفعلة، سيتم التثبيت داخل `.venv` وليس على النظام.

---

### 3️⃣ إعداد ملف البيئة (.env)

تأكد من وجود ملف `.env` في المجلد الرئيسي ويحتوي على (اختر أحد طريقتي Firebase):

```env
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_CHANNEL_ID=your_channel_id_here
ADMIN_PASSWORD=your_admin_password_here
# إما تشير لملف الاعتماد:
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=C:\path\to\firebase-credentials.json
# أو تضع الـ JSON خاماً:
# FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

---

### 4️⃣ تشغيل المشروع

#### تشغيل Dashboard (لوحة التحكم):
```bash
streamlit run dashboard.py
```

**✅ النتيجة:** سيفتح المتصفح تلقائياً على `http://localhost:8501`

#### تشغيل Bot (البوت):
```bash
python bot.py
```

**✅ علامة النجاح:** ستظهر رسالة `Bot is starting...` في الـ Terminal.

---

## 📋 الخطوات الكاملة (من الصفر)

### إنشاء البيئة الافتراضية (إذا لم تكن موجودة):

```bash
# إنشاء البيئة الافتراضية
python -m venv .venv

# تفعيلها
.venv\Scripts\activate  # Windows
# أو
source .venv/bin/activate  # Linux/Mac

# تثبيت المكتبات
pip install -r requirements.txt
```

---

## ☁️ النشر على Streamlit Community Cloud

1. احفظ الكود في مستودع GitHub عام (أو خاص مع خطة مدفوعة).
2. من https://streamlit.io/cloud سجّل الدخول بحساب GitHub.
3. اختر “New app” ثم حدّد المستودع، الفرع (مثل `main`) وملف التشغيل `dashboard.py`.
4. في إعدادات التطبيق، الصق قيمة `requirements.txt` (يُقرأ تلقائياً) وأضف أسرارك من تبويب **Secrets** بالصيغة:
   ```toml
   TELEGRAM_TOKEN = "..."
   TELEGRAM_ADMIN_CHANNEL_ID = "..."
   ADMIN_PASSWORD = "..."
   FIREBASE_SERVICE_ACCOUNT_JSON = """{
       "type": "...",
       ...
   }"""
   ```
   - ضع ملف اعتماد Firebase كـ JSON داخل secrets أو استعمل تخزين خارجي آمن.
5. اضغط Deploy وانتظر حتى يظهر الرابط العام. أي دفع (push) جديد إلى GitHub يعيد النشر تلقائياً.

> راجع الملف `streamlit_secrets_template.toml` كنموذج جاهز لنسخ الأسرار.

### إعداد GitHub سريعاً
```bash
git init
git add .
git commit -m "Prepare Streamlit deploy"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

> **تذكير:** ملف `.gitignore` جاهز ليتجاهل `.venv`, `.env`, `firebase-credentials.json`, و `.streamlit/`.

---

## 🔧 استكشاف الأخطاء

### المشكلة: `'venv' is not recognized`
**الحل:** تأكد من أنك في المجلد الصحيح وأن `.venv` موجود.

### المشكلة: `streamlit: command not found`
**الحل:** 
1. تأكد من تفعيل `.venv`
2. قم بتثبيت المكتبات: `pip install -r requirements.txt`

### المشكلة: `ModuleNotFoundError`
**الحل:** 
```bash
# تأكد من تفعيل venv ثم:
pip install -r requirements.txt
```

### المشكلة: `Permission denied` على Windows
**الحل:** 
```powershell
# في PowerShell كـ Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📁 هيكل المشروع

```
bot/
├── .venv/              # البيئة الافتراضية
├── bot.py              # ملف البوت الرئيسي
├── dashboard.py        # لوحة التحكم (Streamlit)
├── db.py               # طبقة الوصول للبيانات (Firebase)
├── strings.py          # النصوص العربية
├── requirements.txt    # المكتبات المطلوبة
├── .env                # ملف الإعدادات (يجب إنشاؤه)
└── firebase-credentials.json  # بيانات Firebase
```

---

## 🎯 سيناريوهات الاستخدام

### السيناريو 1: تشغيل Dashboard فقط
```bash
.venv\Scripts\activate
streamlit run dashboard.py
```

### السيناريو 2: تشغيل Bot فقط
```bash
.venv\Scripts\activate
python bot.py
```

### السيناريو 3: تشغيل الاثنين معاً
افتح **Terminal 1**:
```bash
.venv\Scripts\activate
streamlit run dashboard.py
```

افتح **Terminal 2**:
```bash
.venv\Scripts\activate
python bot.py
```

---

## ⚠️ ملاحظات مهمة

1. **لا تنس تفعيل `.venv`** قبل تشغيل أي أمر
2. **تأكد من وجود ملف `.env`** مع جميع المتغيرات المطلوبة
3. **Dashboard يعمل على المنفذ 8501** - إذا كان مشغول، سيستخدم 8502 تلقائياً
4. **Bot يحتاج اتصال بالإنترنت** للاتصال بـ Telegram API و Firebase

---

## 🆘 الحصول على المساعدة

إذا واجهت أي مشكلة:
1. تأكد من تفعيل `.venv`
2. تأكد من تثبيت جميع المكتبات
3. تحقق من ملف `.env`
4. راجع رسائل الخطأ في الـ Terminal

---

**آخر تحديث:** 2025-01-19



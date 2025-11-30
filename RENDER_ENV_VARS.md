# 🔐 Environment Variables المطلوبة في Render

## 📋 قائمة المتغيرات (للـ Bot على Render):

### ✅ **متغيرات مطلوبة (Required):**

| المتغير | القيمة | الوصف |
|---------|--------|-------|
| `TELEGRAM_TOKEN` | `8463136615:AAHR3wZB5a72F_kS8VLb1lMz7S-NA_9momA` | توكن البوت من @BotFather |
| `TELEGRAM_ADMIN_CHANNEL_ID` | `-1003070315274` | معرف القناة الخاصة بالإدارة |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | (انظر أدناه) | بيانات Firebase كـ JSON string |

### ⚠️ **متغيرات اختيارية (Optional):**

| المتغير | القيمة الافتراضية | الوصف |
|---------|-------------------|-------|
| `PORT` | `5000` | منفذ الـ health check server (Render بيحدده تلقائياً) |

---

## 📝 **كيفية إضافة المتغيرات في Render:**

### 1. في Render Dashboard:
- ادخل على الـ service (`menouf_bot`)
- اضغط **"Environment"** من القائمة الجانبية
- اضغط **"Add Environment Variable"**

### 2. أضف المتغيرات واحدة واحدة:

#### **المتغير الأول: `TELEGRAM_TOKEN`**
```
Key: TELEGRAM_TOKEN
Value: 8463136615:AAHR3wZB5a72F_kS8VLb1lMz7S-NA_9momA
```

#### **المتغير الثاني: `TELEGRAM_ADMIN_CHANNEL_ID`**
```
Key: TELEGRAM_ADMIN_CHANNEL_ID
Value: -1003070315274
```

#### **المتغير الثالث: `FIREBASE_SERVICE_ACCOUNT_JSON`** ⚠️ (مهم جداً)
```
Key: FIREBASE_SERVICE_ACCOUNT_JSON
Value: [ضع هنا محتوى ملف firebase-credentials.json كـ JSON string في سطر واحد]
```

**⚠️ ملاحظة مهمة:**
- الـ JSON لازم يكون **سطر واحد** (بدون أسطر جديدة)
- كل `\n` في `private_key` لازم تفضل كما هي (مش تتحول لسطر جديد)
- انسخ الـ JSON من `firebase-credentials.json` وضغطه في سطر واحد

### 3. بعد إضافة كل المتغيرات:
- اضغط **"Save Changes"**
- Render بيبدأ **re-deploy** تلقائياً
- انتظر **1-2 دقيقة** لحد ما يكمل

---

## ✅ **التحقق من الإعداد:**

### 1. في Render Logs:
بعد الـ deploy، شوف الـ logs:
```
✅ Health check server started on port 5000
✅ Bot is starting...
✅ Cache MISS for taxonomy: programs. Fetching from Firestore.
```

### 2. في Telegram:
- جرب `/start` في البوت
- تأكد إن يرد بسرعة

### 3. في Browser:
- افتح: `https://menouf-bot.onrender.com/health`
- المفروض يظهر: `{"status": "healthy", "bot": "online"}`

---

## 🔧 **استكشاف الأخطاء:**

### ❌ "TELEGRAM_TOKEN not set"
**الحل:** تأكد إن `TELEGRAM_TOKEN` موجود في Environment Variables

### ❌ "Failed to initialize Firebase"
**الحل:** 
- تأكد إن `FIREBASE_SERVICE_ACCOUNT_JSON` صحيح
- تأكد إن الـ JSON **سطر واحد** (بدون أسطر جديدة)
- جرب تحويل `firebase-credentials.json` إلى JSON string واحد

### ❌ "Invalid FIREBASE_SERVICE_ACCOUNT_JSON"
**الحل:**
- الـ JSON مش صحيح أو فيه أخطاء
- استخدم online JSON validator: https://jsonlint.com/
- تأكد إن كل الـ quotes مضاعفة (`"` مش `'`)

---

## 📝 **ملخص سريع:**

```
✅ TELEGRAM_TOKEN = "8463136615:AAHR3wZB5a72F_kS8VLb1lMz7S-NA_9momA"
✅ TELEGRAM_ADMIN_CHANNEL_ID = "-1003070315274"
✅ FIREBASE_SERVICE_ACCOUNT_JSON = "{...JSON كامل في سطر واحد...}"
⏭️ PORT = "5000" (اختياري - Render بيحدده تلقائياً)
```

---

**آخر تحديث:** 2025-01-19


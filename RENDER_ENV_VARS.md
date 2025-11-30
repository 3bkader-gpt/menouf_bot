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
Value: {"type":"service_account","project_id":"menofbot","private_key_id":"e0298011207f5ccb1d07c028f278e29789387874","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC0Hq6xy5SKylwA\n2cOLrC3ORIh6Zyrxt1Q7l/cNy+gZlxSRSpE8r+tKm+skXojAV3BTFu7OMvwaEiqR\nAVZEqXbYG6UpLbgKy2rsOCkRb/Z9VKjNMH+3l/7iDBWdutyJ+QKIQ5Os6P/fSy1K\nhDB8uDL+qNUF5F6ti2Nn5KK+M/FdaAPXZzVyPC/APY+Qbt1MNe48b2VCc9yEVPfG\nsuGFnOR40g1mrEovHpmm7z66r5Wl2BCiHg66haJp/ptIkiUv7EjEEBfDotP1b1iF\nze6uSNxV6O5feicyzkFmosrKJQcDLmNHfzMVDW8qSov9ugyIs8wusXBY6N3eteUu\nz77ywiblAgMBAAECggEAN8q5OgFhRYxg6zKIy57NoXLBA4kpWC39PWhY8kES57pQ\neKCsVCv5qeaZ824E1e8/r70Ow3gvdrPh04CihCop0c7eXd73fwB7YigTMH+JzlCG\n6Of455mBLeuoVm8nGOW0zxh/ibOybiwPH2HK0xcLVK5fLbALU541cFz1vAzC2rd0\nTvYTyARXkf4x92Pu4bIg5/tKF/yDZc2OTgHC+E3vainHumy0bJz37fCblniDaeB9\npnr+KkROBbp77DXRLFSXADBtnLm/8aPW/ntxFrHLQWcTnNJhUCNDRlyIyLjrrylP\nLUhK9SDuy028Gai/BpYqgjkkAFHhsU876tHqF64XEQKBgQDZeFXVEqGDROvMTkBK\nFIEGnLMCSccv07YWFVX7PQjqdvvMEKamQlVSoR2ccRDT/oSAfuFwkAkpqUg6jdLK\nqrK2JfT1Owdgj+y8oTK4QLixkHeLGLz5yaHjyD6/vq5itDo0DYVtmxHpRp8y01En\nfZzlv7Kuzky0mNCDR6TUrHgzkwKBgQDUCEZ1bq9pQwCZkoOk8/+62qa4YZBVSvcb\nDWvRhnXqeCl2gC/tJu4LNe9gUb2AzcP077ncS9k7vbrYs0KKD7hYZWo1FQywCYEW\ncOiy8heITak3PZVmrsciICIsxolM/WzD2a+d3ExIpeuFDxv1v5x11s/duIpHZd2M\nWbON/lq2pwKBgQCtXsDWwCag9xYg55VbOaNvOQeA4H56g4abbmEAjTUJbtfoZLHm\nw+UvnaB0srLevv61TfG+AiY732fkvmH5DkKw8euqgWetNLBf5QcBWx+i93BGJO+r\nF3MHnAFibcqqh9IK42im68RIu/N42nzNRdgKVVxG/dKq+1ToA/rFTcX6HwKBgFfp\nunUUWIyXaFdEhWrOdFjgMcI/SZ3jwEMqNGsiih+WhPKKQdTdkFN7oG3aVm1iY35a\nK0Do/gAkMaWJ5eviire0DO5HdQREXI6WcBVKBXHRaXjrAtgZXZ2Lnz/bbbBLX15x\nErysS8DPcrCvzBL/yHqff35Z9pOV6982jhkwviH/AoGAeMXaxeXU84A6uPZXyJWV\nXoKa3XdraTrGjo6rZW8daba9ugvoO34ORI56A92O9XccHF6yFBxgfSb/vOeJ+uB9\nv05YCsocMhtCRCX+7BZiG3bcQ+MVd3Sh5Rs/yMFM85p0gVG0Ev2//oOmeojbLfKk\nh1ll9HFx52hAmTrYCCaS8fE=\n-----END PRIVATE KEY-----\n","client_email":"firebase-adminsdk-fbsvc@menofbot.iam.gserviceaccount.com","client_id":"109540090647673719660","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40menofbot.iam.gserviceaccount.com","universe_domain":"googleapis.com"}
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


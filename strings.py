"""
Centralized Arabic strings for the Telegram bot.

This module contains all user-facing Arabic text to improve maintainability
and make localization easier in the future.
"""


class Strings:
    """Central repository for all Arabic strings used in the bot."""
    
    # Main menu strings
    WELCOME = "حبيبي يا هندسه, ده بوت فيه ماتريال لكليه هندسه منوف "
    BROWSE = "شوف الماتريال"
    SEARCH = "بحث سريع"
    MAIN_MENU = "القائمة الرئيسية"
    BACK = "رجوع"
    
    # Navigation prompts
    SELECT_PROGRAM = "اختار القسم 👇"
    SELECT_SUBJECT = "اختار المادة 👇"
    SELECT_LECTURE = "اختار المحاضرة 👇"
    
    # Breadcrumb templates
    BREADCRUMB_PROGRAM = "القسم: *{program}*\n\n{prompt}"
    BREADCRUMB_SUBJECT = "{program} > المادة: *{subject}*\n\n{prompt}"
    BREADCRUMB_LECTURE = "{program} > {subject} > المحاضرة: *{lecture}*\n\n"
    
    # File management
    FILES_AVAILABLE = "📁 **الملفات المتاحة:**"
    NO_FILES_AVAILABLE = "❌ لا توجد ملفات متاحة."
    DOWNLOAD_FILE = "⬇️ تحميل ({number})"
    REPORT_PROBLEM = "⚠️ إبلاغ عن مشكلة"
    FILE_NOT_FOUND = "عذراً، الملف غير موجود"
    FILE_ERROR = "عفوًا، حدث خطأ أثناء جلب الملف. يبدو أن الملف لم يعد متاحًا."
    
    # Search functionality
    SEARCH_PROMPT = "أدخل نص البحث (اسم الملف):"
    SEARCH_NO_RESULTS = "😥 مفيش نتايج مطابقة للبحث ده. جرب كلمة تانية."
    SEARCH_RESULTS = "🔍 دي النتايج المطابقة لكلمة '{query}':"
    
    # Error messages
    GENERIC_ERROR = "عذراً، حدث خطأ. الرجاء المحاولة مرة أخرى."
    UNKNOWN_BUTTON = "هذا الزر غير معرف حالياً."
    NO_YEARS_AVAILABLE = "لا توجد بيانات متاحة حالياً."
    ERROR_STATE_LOST = "عذراً، حدث خطأ في حالة التنقل. الرجاء البدء من جديد."
    
    # Special values
    YEAR_PREP = "إعدادي"
    PROGRAM_NONE = ""
    
    # Taxonomy document keys
    TAX_DOC_PROGRAMS = "programs"
    TAX_DOC_TERMS = "terms"
    TAX_DOC_SUBJECTS = "subjects"
    TAX_DOC_LECTURES = "lectures"
    
    # Report system
    RATE_LIMIT_EXCEEDED = "⚠️ لقد تجاوزت الحد المسموح (3 بلاغات/ساعة). حاول مرة أخرى لاحقًا."
    REPORT_SUCCESS = "✅ شكرًا لإبلاغك! هيتم مراجعة الملف."
    REPORT_ERROR = "حدث خطأ أثناء إرسال البلاغ."
    REPORT_ADMIN_ALERT = "⚠️ *إبلاغ عن مشكلة في ملف\\!* ⚠️\n\n• *الملف:* {file_name}\n• *ID:* `{doc_id}`\n• *المستخدم:* {user_name} {user_mention}"
    
    # Inline mode
    INLINE_FILE_CAPTION = "ملف: {file_name}"
    
    # Button labels with emojis
    BTN_MAIN_MENU = "🏠 القائمة الرئيسية"
    BTN_BACK = "🔙 رجوع"
    BTN_BACK_TO_MAIN = "🔙 رجوع للقائمة الرئيسية"

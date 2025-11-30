"""
Admin Dashboard (Streamlit) for Uploader Bot — Dual Upload System

- Simple password protection (ADMIN_PASSWORD from .env, fallback 'admin').
- Uses the same Firebase init function from db.py (init_firebase).
- Dual Upload System: Direct upload (up to 48MB) OR File ID input (up to 2GB)
- File validation for security and size limits
- Sends uploaded files to a private admin channel to obtain Telegram file_id,
  then saves a document into the 'files' collection in Firestore.
- Uses python-telegram-bot to send the document (async), executed from Streamlit
  using a dedicated event loop to avoid interfering with Streamlit's runtime.

Usage:
  1. Create a .env with TELEGRAM_TOKEN, TELEGRAM_ADMIN_CHANNEL_ID, ADMIN_PASSWORD,
     and either FIREBASE_SERVICE_ACCOUNT_KEY_PATH or FIREBASE_SERVICE_ACCOUNT_JSON.
  2. Run: streamlit run dashboard.py
"""

import os
import io
import asyncio
import logging
from dotenv import load_dotenv

import streamlit as st
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional

# Telegram async Bot
from telegram import Bot as TgBot

# Reuse the project's db module to initialize Firestore
import db as db_module
from firebase_admin import firestore

# Load environment
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHANNEL_ID = os.getenv("TELEGRAM_ADMIN_CHANNEL_ID")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")  # simple password protection

# Security Constants
ALLOWED_EXTENSIONS = {'.pdf', '.zip', '.rar', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.mp3', '.m4a', '.mp4', '.mkv', '.mov', '.avi'}
# Set max limit slightly below Telegram's 50MB Bot API limit
MAX_FILE_SIZE_MB = 48

DEFAULT_YEAR_KEY = "تانيه"

# Basic validations
if not TELEGRAM_TOKEN:
    st.error("Environment error: TELEGRAM_TOKEN not set.")
    st.stop()
if not TELEGRAM_ADMIN_CHANNEL_ID:
    st.error("Environment error: TELEGRAM_ADMIN_CHANNEL_ID not set.")
    st.stop()
if not (FIREBASE_KEY_PATH or FIREBASE_KEY_JSON):
    st.error("Environment error: provide FIREBASE_SERVICE_ACCOUNT_KEY_PATH or FIREBASE_SERVICE_ACCOUNT_JSON.")
    st.stop()


# Initialize Firebase on app start (safe to call multiple times)
try:
    db_module.init_firebase(FIREBASE_KEY_PATH, FIREBASE_KEY_JSON)
    firestore_client: firestore.Client = db_module.db
except ValueError as e:
    if "already exists" in str(e).lower():
        try:
            firestore_client = firestore.client()
            db_module.db = firestore_client
        except Exception as inner_e:
            st.error(f"Failed to reuse Firebase client: {inner_e}")
            st.stop()
    else:
        st.error(f"Failed to initialize Firebase: {e}")
        st.stop()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.stop()


# ----------------- File Validation -----------------

def validate_file_uploaded(uploaded_file, file_id_input: str) -> tuple[bool, str]:
    """Validates file or ID input."""
    if uploaded_file is None and not file_id_input:
        return False, "يجب إدخال ملف أو File ID"
    
    if uploaded_file:
        # 1. Check size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, f"حجم الملف كبير ({file_size_mb:.1f}MB). الحد الأقصى للرفع المباشر هو {MAX_FILE_SIZE_MB}MB. استخدم خاصية File ID للملفات الأكبر."
        
        # 2. Check extension
        filename = uploaded_file.name.lower()
        ext = os.path.splitext(filename)[1]
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"نوع الملف غير صالح: {ext}. الأنواع المسموح بها هي: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, ""


# ----------------- Helper: send file to Telegram (async) -----------------


async def _async_send_document(token: str, chat_id: str, file_bytes: bytes, filename: str):
    """
    Async helper that uses python-telegram-bot's Bot to send a document and return the Message.
    """
    bot = TgBot(token=token)
    # Provide file as bytes. telegram accepts bytes/bytearray/file-like; include filename metadata.
    # Note: send_document is coroutine in PTB v20+
    return await bot.send_document(chat_id=chat_id, document=file_bytes, filename=filename)


def send_document_and_get_file_id(token: str, chat_id: str, file_bytes: bytes, filename: str):
    """
    Synchronous wrapper for Streamlit: runs the async send in a new event loop and returns file_id.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        message = loop.run_until_complete(_async_send_document(token, chat_id, file_bytes, filename))
    finally:
        try:
            loop.close()
        except Exception:
            pass

    # Extract file_id from returned message
    doc = getattr(message, "document", None)
    if not doc:
        raise RuntimeError("Telegram did not return document metadata.")
    return doc.file_id


# ----------------- Streamlit UI -----------------

st.set_page_config(page_title="Uploader Bot - Admin Dashboard", layout="centered")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'last_attempt' not in st.session_state:
    st.session_state.last_attempt = datetime.now()
if 'file_edit_context' not in st.session_state:
    st.session_state.file_edit_context = None
if 'file_delete_context' not in st.session_state:
    st.session_state.file_delete_context = None
if 'manage_files_results' not in st.session_state:
    st.session_state.manage_files_results = []


def verify_password(password: str) -> bool:
    """Securely verify admin password"""
    return hmac.compare_digest(password, ADMIN_PASSWORD)

def check_rate_limit() -> bool:
    """Check if user is rate limited"""
    if st.session_state.login_attempts >= 3:
        time_passed = datetime.now() - st.session_state.last_attempt
        if time_passed < timedelta(minutes=15):
            return False
        st.session_state.login_attempts = 0
    return True

def login_form():
    """Display login form with rate limiting"""
    st.title("تسجيل دخول لوحة التحكم")
    
    if not check_rate_limit():
        st.error("Too many login attempts. Please wait 15 minutes.")
        return
    
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        st.session_state.last_attempt = datetime.now()
        if verify_password(password):
            st.session_state.authenticated = True
            st.session_state.login_attempts = 0
            st.rerun()  # Changed from st.experimental_rerun()
        else:
            st.session_state.login_attempts += 1
            st.error("Invalid password")

# Dual Upload System
async def upload_file(file_data: dict, uploaded_file, file_id_input: str) -> str:
    """Handles dual upload logic and returns the final doc_id."""
    manual_file_id = (file_id_input or "").strip()

    if manual_file_id:
        final_file_id = manual_file_id
    elif uploaded_file:
        file_bytes = uploaded_file.getvalue()
        final_file_id = await asyncio.to_thread(
            send_document_and_get_file_id,
            TELEGRAM_TOKEN,
            TELEGRAM_ADMIN_CHANNEL_ID,
            file_bytes,
            uploaded_file.name,
        )
    else:
        raise ValueError("Invalid upload state.")

    file_data['file_id'] = final_file_id
    return await db_module.save_file(file_data)

# Dynamic configuration loaded from Firebase

def load_initial_data():
    """Load configuration data from Firebase and cache in session state."""
    if 'config_data' not in st.session_state:
        try:
            # Fetch configuration from Firebase
            config_data = asyncio.run(db_module.get_all_taxonomy_config())
            st.session_state.config_data = config_data
            logging.info("Configuration loaded from Firebase")
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            # Fallback to minimal defaults
            st.session_state.config_data = {
                'YEAR_OPTIONS': ["إعدادي", "أولي", "تانيه", "تالته", "رابعه"],
                'PROGRAM_OPTIONS': ["تحكم", "حاسبات", "اتصالات"],
                'TERM_OPTIONS': ["اول", "تاني"],
                'SUBJECTS_BY_PROGRAM': {},
                'YEAR_RULES': {}
            }

def get_config(key: str, default=None):
    """Get a configuration value from session state."""
    return st.session_state.config_data.get(key, default)

def get_year_rule(year: str, rule_key: Optional[str] = None, default=None):
    """Retrieve a specific rule (or full rule dict) for a given year."""
    year_rules = get_config('YEAR_RULES', {}) or {}
    if rule_key is None:
        return year_rules.get(year, {})
    return year_rules.get(year, {}).get(rule_key, default)

def requires_program(year: str) -> bool:
    """Check if a year requires program selection."""
    return bool(get_year_rule(year, 'REQUIRES_PROGRAM', True))

def requires_term(year: str) -> bool:
    """Check if a year requires term selection."""
    return bool(get_year_rule(year, 'REQUIRES_TERM', True))

def get_subject_input_type(year: str) -> str:
    """Get the subject input type for a year."""
    return str(get_year_rule(year, 'SUBJECT_INPUT', 'TEXT')).upper()

def get_info_message(year: str):
    """Get the info message for a year."""
    return get_year_rule(year, 'INFO_MESSAGE')

def get_subjects_for_program(program: str, subjects_key: str = 'SUBJECTS_BY_PROGRAM') -> list:
    """Get subject list for a specific program from the configured source."""
    subjects_source = get_config(subjects_key, {})

    if isinstance(subjects_source, dict):
        general_subjects = subjects_source.get("عام", [])
        specific_subjects = subjects_source.get(program, [])
        combined = []
        for entry in list(general_subjects) + list(specific_subjects):
            value = str(entry).strip()
            if value:
                combined.append(value)
        return sorted(set(combined))

    if isinstance(subjects_source, list):
        return sorted({str(entry).strip() for entry in subjects_source if str(entry).strip()})

    return []

def render_taxonomy_selectors(label_overrides: Optional[dict] = None):
    """Render selection widgets dynamically using Year -> Program -> Term -> Subject."""
    default_labels = {
        'year': "الفرقة",
        'program': "التخصص",
        'term': "الترم",
        'subject': "المادة",
    }
    labels = default_labels | (label_overrides or {})

    years_doc = fetch_taxonomy_doc("years")
    year_options = dedupe_options(
        (years_doc.get('list', []) if isinstance(years_doc, dict) else []) + (get_config('YEAR_OPTIONS', []) or [])
    )
    if not year_options:
        st.error("لا توجد فرق متاحة حالياً. الرجاء تحديث الإعدادات في Firebase.")
        return {
            'year': '',
            'program': '',
            'term': '',
            'subject': '',
            'rules': {},
            'subjects_list_key': 'SUBJECTS_BY_PROGRAM',
            'subject_input_type': 'TEXT',
        }

    selected_year = st.selectbox(labels['year'], year_options)
    year_rules = get_year_rule(selected_year)
    subjects_list_key = get_year_rule(selected_year, 'SUBJECTS_LIST_KEY', 'SUBJECTS_BY_PROGRAM')
    subject_input_type = get_subject_input_type(selected_year)
    candidate_years = get_candidate_years(selected_year, years_doc)

    # Program selection
    selected_program = ""
    programs_doc = fetch_taxonomy_doc("programs")
    if requires_program(selected_year):
        program_options = [""] + get_program_options(programs_doc, selected_year, years_doc)
        selected_program = st.selectbox(labels['program'], program_options)
        if not selected_program:
            st.info("يرجى اختيار التخصص للمتابعة.")
            return {
                'year': selected_year,
                'program': '',
                'term': '',
                'subject': '',
                'rules': year_rules,
                'subjects_list_key': subjects_list_key,
                'subject_input_type': subject_input_type,
            }
    else:
        selected_program = ""
        info_msg = get_info_message(selected_year)
        if info_msg:
            st.info(info_msg)

    # Term selection
    selected_term = ""
    if requires_term(selected_year):
        terms_doc = fetch_taxonomy_doc("terms")
        found_terms = get_term_options(terms_doc, candidate_years, selected_program)
        # Hard fallback: if no terms found in DB, use default terms
        if not found_terms:
            found_terms = get_config('TERM_OPTIONS', ["اول", "تاني"]) or ["اول", "تاني"]
        term_options = [""] + sorted(dedupe_options(found_terms))
        selected_term = st.selectbox(labels['term'], term_options)
        if not selected_term:
            st.info("يرجى اختيار الترم للمتابعة.")
            return {
                'year': selected_year,
                'program': selected_program,
                'term': '',
                'subject': '',
                'rules': year_rules,
                'subjects_list_key': subjects_list_key,
                'subject_input_type': subject_input_type,
            }
    else:
        selected_term = get_year_rule(selected_year, 'DEFAULT_TERM', '')

    # Subject selection / input
    selected_subject = ""
    subject_widget_key = f"subject_input_{selected_year}_{selected_program or 'general'}_{subject_input_type}"

    if subject_input_type == "DROPDOWN":
        subjects_doc = fetch_taxonomy_doc("subjects")
        subject_options = get_subject_options(subjects_doc, candidate_years, selected_program, selected_term)
        if not subject_options:
            subject_options = get_subjects_for_program(selected_program or selected_year, subjects_list_key)
        subject_options_with_blank = [""] + subject_options
        selected_subject = st.selectbox(labels['subject'], subject_options_with_blank, key=subject_widget_key)
    elif subject_input_type == "MULTISELECT":
        subject_options = get_subjects_for_program(selected_program or selected_year, subjects_list_key)
        multi_selected = st.multiselect(labels['subject'], subject_options, key=subject_widget_key)
        selected_subject = ", ".join(multi_selected)
    else:
        selected_subject = st.text_input(labels['subject'], key=subject_widget_key)

    return {
        'year': selected_year,
        'program': selected_program,
        'term': selected_term,
        'subject': selected_subject.strip(),
        'rules': year_rules,
        'subjects_list_key': subjects_list_key,
        'subject_input_type': subject_input_type,
        'candidate_years': candidate_years,
    }

def manage_subjects_page():
    """Admin page for managing subject lists."""
    st.title("إدارة قوائم المواد")
    st.markdown("---")
    
    year_options = get_config('YEAR_OPTIONS', [])
    if not year_options:
        st.info("لا توجد بيانات فرق متاحة للتحرير.")
        return

    col1, col2 = st.columns(2)

    with col1:
        year = st.selectbox("اختر الفرقة", year_options)

    subjects_list_key = get_year_rule(year, 'SUBJECTS_LIST_KEY', 'SUBJECTS_BY_PROGRAM')
    if subjects_list_key:
        st.caption(f"يتم تحميل المواد من القائمة: `{subjects_list_key}`")

    programs_doc = fetch_taxonomy_doc("programs")

    with col2:
        if requires_program(year):
            program_options = get_program_options(programs_doc, year)
            if not program_options:
                st.warning("لا توجد تخصصات معرفة. الرجاء إضافتها في الإعدادات.")
                return
            program = st.selectbox("اختر التخصص", program_options)
        else:
            available_groups = ["عام"] + get_program_options(programs_doc, year)
            program = st.selectbox("اختر المجموعة", available_groups)

    program_key = program or "عام"

    # Display current subjects
    st.subheader(f"المواد الحالية - {program_key}")
    current_subjects = get_subjects_for_program(program_key, subjects_list_key)

    if current_subjects:
        st.write("المواد المسجلة حاليًا:")
        cols = st.columns(3)
        for i, subject in enumerate(current_subjects):
            cols[i % 3].markdown(f"- 📚 **{subject}**")
    else:
        st.info("لا توجد مواد مضافة حتى الآن.")

    st.markdown("---")

    # Form to add new subject
    with st.form("add_subject_form"):
        st.subheader("إضافة مادة جديدة")
        new_subject = st.text_input("اسم المادة الجديدة")
        submit = st.form_submit_button("إضافة المادة")

    if submit:
        if new_subject and new_subject.strip():
            try:
                new_subject_value = new_subject.strip()
                if subjects_list_key == 'SUBJECTS_BY_PROGRAM':
                    asyncio.run(db_module.update_subject_list(program_key, new_subject_value))
                else:
                    doc_ref = firestore_client.collection('config').document('taxonomy_lists')
                    asyncio.run(
                        asyncio.to_thread(
                            doc_ref.update,
                            {f'{subjects_list_key}.{program_key}': firestore.ArrayUnion([new_subject_value])}
                        )
                    )
                st.success(f"تم إضافة المادة '{new_subject}' بنجاح!")

                # Clear cache and reload
                if 'config_data' in st.session_state:
                    del st.session_state.config_data
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"فشل في إضافة المادة: {str(e)}")
                logging.exception("Failed to add subject")
        else:
            st.error("يرجى إدخال اسم المادة")


def manage_files_page():
    """Main router for file management: browse, edit, delete."""
    st.title("إدارة الملفات")

    if st.session_state.get("confirm_delete_lecture"):
        path = st.session_state.get('last_path', {})
        lecture_name = st.session_state.get('last_selected_lecture', '')
        st.warning(f"هل أنت متأكد أنك تريد حذف فولدر '{lecture_name}' وكل الملفات بداخله؟ هذا لا يمكن التراجع عنه.")

        c1, c2 = st.columns(2)
        if c1.button("نعم، احذف الفولدر الآن", use_container_width=True):
            try:
                asyncio.run(db_module.delete_lecture_and_files(
                    path.get('program', ''),
                    path.get('term', ''),
                    path.get('subject', ''),
                    path.get('lecture', '')
                ))
                st.success("تم حذف الفولدر بنجاح.")
                st.session_state.confirm_delete_lecture = False
                st.session_state.manage_files_results = []
                st.rerun()
            except Exception as e:
                st.error(f"فشل الحذف: {e}")

        if c2.button("إلغاء", use_container_width=True):
            st.session_state.confirm_delete_lecture = False
            st.rerun()

        return

    delete_context = st.session_state.get('file_delete_context')
    if delete_context:
        render_delete_confirmation(delete_context)
        return

    edit_context = st.session_state.get('file_edit_context')
    if edit_context:
        render_edit_form(edit_context)
        return

    render_browse_view()


def fetch_taxonomy_doc(doc_key: str):
    try:
        return asyncio.run(db_module.get_taxonomy_doc(doc_key))
    except Exception as exc:
        st.error(f"فشل في تحميل {doc_key}: {exc}")
        return {}


def extract_program_list(doc: dict) -> list[str]:
    """Return combined program list supporting legacy/year-based structures."""
    if not isinstance(doc, dict):
        return []
    programs: list[str] = []
    base_list = doc.get('list')
    if isinstance(base_list, list):
        programs.extend(base_list)
    for key, value in doc.items():
        if key == 'list':
            continue
        if isinstance(value, list):
            programs.extend(value)
    return dedupe_options(programs)


def dedupe_options(options: list[str]) -> list[str]:
    seen = set()
    result = []
    for option in options or []:
        value = str(option).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def get_candidate_years(preferred_year: str = "", years_doc: Optional[dict] = None) -> list[str]:
    candidates: list[str] = []
    if preferred_year:
        candidates.append(preferred_year)
    if isinstance(years_doc, dict):
        doc_years = years_doc.get('list')
        if isinstance(doc_years, list):
            candidates.extend(doc_years)
    config_years = get_config('YEAR_OPTIONS', [])
    if isinstance(config_years, list):
        candidates.extend(config_years)
    candidates.append(DEFAULT_YEAR_KEY)
    return dedupe_options(candidates)


def get_program_options(programs_doc: dict, selected_year: str, years_doc: Optional[dict] = None) -> list[str]:
    options: list[str] = []
    options.extend(extract_program_list(programs_doc))
    if isinstance(programs_doc, dict) and selected_year:
        year_bucket = programs_doc.get(selected_year)
        if isinstance(year_bucket, list):
            options.extend(year_bucket)
    fallback_programs = get_config('PROGRAM_OPTIONS', [])
    if isinstance(fallback_programs, list):
        options.extend(fallback_programs)
    return sorted(dedupe_options(options))


def get_term_options(terms_doc: dict, candidate_years: list[str], selected_program: str) -> list[str]:
    if not isinstance(terms_doc, dict):
        return []
    options: list[str] = []
    if selected_program:
        direct = terms_doc.get(selected_program)
        if isinstance(direct, list):
            options.extend(direct)
    for year in candidate_years:
        if selected_program:
            legacy_key = f"{year}_{selected_program}"
        else:
            legacy_key = year
        values = terms_doc.get(legacy_key)
        if isinstance(values, list):
            options.extend(values)
    suffix = f"_{selected_program}" if selected_program else ""
    if suffix:
        for key, values in terms_doc.items():
            if isinstance(values, list) and key.endswith(suffix):
                options.extend(values)
    return sorted(dedupe_options(options))


def _merge_subject_keys(candidate_years: list[str], selected_program: str, selected_term: str) -> list[str]:
    keys: list[str] = []
    if selected_program and selected_term:
        keys.append(f"{selected_program}_{selected_term}")
    if selected_term:
        keys.append(selected_term)
    for year in candidate_years:
        parts = [year]
        if selected_program:
            parts.append(selected_program)
        if selected_term:
            parts.append(selected_term)
        legacy_key = "_".join(filter(None, parts))
        if legacy_key:
            keys.append(legacy_key)
        if not selected_program and selected_term:
            fallback_key = f"{year}_{selected_term}"
            keys.append(fallback_key)
    return dedupe_options(keys)


def get_subject_options(subjects_doc: dict, candidate_years: list[str], selected_program: str, selected_term: str) -> list[str]:
    if not isinstance(subjects_doc, dict) or not selected_term:
        return []
    options: list[str] = []
    for key in _merge_subject_keys(candidate_years, selected_program, selected_term):
        values = subjects_doc.get(key)
        if isinstance(values, list):
            options.extend(values)
    suffix_parts = [selected_program, selected_term]
    suffix = "_".join(filter(None, suffix_parts))
    if suffix:
        for key, values in subjects_doc.items():
            if isinstance(values, list) and key.endswith(suffix):
                options.extend(values)
    return sorted(dedupe_options(options))


def get_lecture_options(lectures_doc: dict, candidate_years: list[str], selected_program: str, selected_term: str, selected_subject: str) -> list[str]:
    if not isinstance(lectures_doc, dict) or not selected_subject:
        return []
    options: list[str] = []
    base_keys: list[str] = []
    base_keys.append("_".join(filter(None, [selected_program, selected_term, selected_subject])))
    base_keys.append("_".join(filter(None, [selected_term, selected_subject])))
    base_keys.append(selected_subject)
    for year in candidate_years:
        parts = [year]
        if selected_program:
            parts.append(selected_program)
        parts.extend([selected_term, selected_subject])
        legacy_key = "_".join(filter(None, parts))
        base_keys.append(legacy_key)
    for key in dedupe_options(base_keys):
        if not key:
            continue
        values = lectures_doc.get(key)
        if isinstance(values, list):
            options.extend(values)
    suffix = "_".join(filter(None, [selected_program, selected_term, selected_subject]))
    if suffix:
        for key, values in lectures_doc.items():
            if isinstance(values, list) and key.endswith(suffix):
                options.extend(values)
    return sorted(dedupe_options(options))


def render_browse_view():
    st.caption("ابدأ بـ 'المستكشف' لاختيار مسار الملفات.")

    years_doc = fetch_taxonomy_doc("years")
    year_options = dedupe_options(
        (years_doc.get('list', []) if isinstance(years_doc, dict) else []) + (get_config('YEAR_OPTIONS', []) or [])
    )
    if not year_options:
        st.error("لا توجد فرق متاحة حالياً.")
        return
    selected_year = st.selectbox("الخطوة 1: اختر الفرقة", year_options)
    candidate_years = get_candidate_years(selected_year, years_doc)

    programs_doc = fetch_taxonomy_doc("programs")
    if requires_program(selected_year):
        program_options = [""] + get_program_options(programs_doc, selected_year, years_doc)
        selected_program = st.selectbox("الخطوة 2: اختر التخصص", program_options)
        if not selected_program:
            st.info("يرجى اختيار التخصص للمتابعة.")
            return
    else:
        selected_program = ""
        info_msg = get_info_message(selected_year)
        if info_msg:
            st.info(info_msg)

    if requires_term(selected_year):
        terms_doc = fetch_taxonomy_doc("terms")
        found_terms = get_term_options(terms_doc, candidate_years, selected_program)
        # Hard fallback: if no terms found in DB, use default terms
        if not found_terms:
            found_terms = get_config('TERM_OPTIONS', ["اول", "تاني"]) or ["اول", "تاني"]
        term_options = [""] + sorted(dedupe_options(found_terms))
        selected_term = st.selectbox("الخطوة 3: اختر الترم", term_options)
        if not selected_term:
            st.info("يرجى اختيار الترم للمتابعة.")
            return
    else:
        selected_term = get_year_rule(selected_year, 'DEFAULT_TERM', '')

    subjects_doc = fetch_taxonomy_doc("subjects")
    subject_options = [""] + get_subject_options(subjects_doc, candidate_years, selected_program, selected_term)
    if not subject_options:
        st.warning("لا توجد مواد متاحة لهذا المسار حالياً.")
        return
    selected_subject = st.selectbox("الخطوة 4: اختر المادة", subject_options)
    if not selected_subject:
        st.info("يرجى اختيار المادة للمتابعة.")
        return

    lectures_doc = fetch_taxonomy_doc("lectures")
    lecture_options = [""] + get_lecture_options(lectures_doc, candidate_years, selected_program, selected_term, selected_subject)
    if not lecture_options:
        st.warning("لا توجد محاضرات مسجلة لهذا المسار بعد.")
        return
    selected_lecture = st.selectbox("الخطوة 5: اختر المحاضرة (الفولدر)", lecture_options)
    if not selected_lecture:
        st.info("يرجى اختيار المحاضرة لعرض الملفات.")
        return

    st.session_state.last_path = {
        'year': selected_year,
        'program': selected_program,
        'term': selected_term,
        'subject': selected_subject,
        'lecture': selected_lecture
    }
    st.session_state.last_selected_lecture = selected_lecture

    st.markdown("---")
    program_label = selected_program or selected_year
    st.subheader(f"الملفات الموجودة في: {selected_year} / {program_label} / {selected_term or 'بدون ترم'} / {selected_subject} / {selected_lecture}")

    st.markdown("---")
    st.subheader(f"إجراءات الفولدر: {selected_lecture}")
    if st.button("❌ حذف هذا الفولدر (المحاضرة) بالكامل", use_container_width=True):
        st.session_state.confirm_delete_lecture = True
        st.rerun()

    if st.button("عرض الملفات", use_container_width=True):
        try:
            files = asyncio.run(
                db_module.get_files(
                    selected_program or '',
                    selected_term or '',
                    selected_subject,
                    selected_lecture
                )
            )
            st.session_state.manage_files_results = files
            st.session_state.file_edit_context = None
            st.session_state.file_delete_context = None
            if not files:
                st.info("لا توجد ملفات في هذا المسار حالياً.")
        except Exception as e:
            st.error(f"فشل في تحميل الملفات: {e}")

    files_list = st.session_state.get('manage_files_results', [])
    if not files_list:
        st.info("لم يتم تحميل أي ملفات بعد. اختر المسار واضغط على زر عرض الملفات.")
        return

    st.subheader("الملفات المتاحة")
    for file in files_list:
        expander_label = f"{file.get('display_name', 'ملف')} ({file.get('file_type', 'FILE')})"
        with st.expander(expander_label, expanded=False):
            st.write(f"الاسم الأصلي: {file.get('original_name')}")
            st.write(f"المسار: {file.get('program')} / {file.get('term')} / {file.get('subject')} / {file.get('lecture')}")
            col_edit, col_delete = st.columns(2)
            if col_edit.button("✏️ تعديل", key=f"edit_{file['id']}"):
                st.session_state.file_edit_context = file
                st.session_state.file_delete_context = None
                st.rerun()
            if col_delete.button("❌ حذف", key=f"delete_{file['id']}"):
                st.session_state.file_delete_context = file
                st.session_state.file_edit_context = None
                st.rerun()


def render_edit_form(file_data: dict):
    st.caption("تعديل الملف باستخدام نفس منطق المستكشف لتجنب الأخطاء.")

    display_name = st.text_input("Display Name (اسم العرض)", value=file_data.get('display_name', ''))

    years_doc = fetch_taxonomy_doc("years")
    year_options = dedupe_options(
        (years_doc.get('list', []) if isinstance(years_doc, dict) else []) + (get_config('YEAR_OPTIONS', []) or [])
    )
    current_year = file_data.get('year') or (year_options[0] if year_options else '')
    if current_year and current_year not in year_options:
        year_options = [current_year] + year_options
    new_year = st.selectbox("الفرقة (جديد)", year_options, index=year_options.index(current_year) if current_year in year_options else 0)
    candidate_years = get_candidate_years(new_year, years_doc)
    year_rules = get_year_rule(new_year)

    programs_doc = fetch_taxonomy_doc("programs")
    if requires_program(new_year):
        program_options = get_program_options(programs_doc, new_year, years_doc)
        if not program_options:
            st.warning("لا توجد تخصصات متاحة لهذه الفرقة حالياً.")
            return
        if file_data.get('program') not in program_options:
            if file_data.get('program'):
                program_options = [file_data.get('program')] + program_options
        new_program = st.selectbox("التخصص (جديد)", program_options, index=program_options.index(file_data.get('program')) if file_data.get('program') in program_options else 0)
    else:
        new_program = ""
        info_msg = get_info_message(new_year)
        if info_msg:
            st.info(info_msg)

    if requires_term(new_year):
        terms_doc = fetch_taxonomy_doc("terms")
        found_terms = get_term_options(terms_doc, candidate_years, new_program)
        # Hard fallback: if no terms found in DB, use default terms
        if not found_terms:
            found_terms = get_config('TERM_OPTIONS', ["اول", "تاني"]) or ["اول", "تاني"]
        term_options = sorted(dedupe_options(found_terms))
        if file_data.get('term') not in term_options:
            if file_data.get('term'):
                term_options = [file_data.get('term')] + term_options
        new_term = st.selectbox("الترم (جديد)", term_options, index=term_options.index(file_data.get('term')) if file_data.get('term') in term_options else 0)
    else:
        new_term = get_year_rule(new_year, 'DEFAULT_TERM', '') or file_data.get('term', '')

    subjects_doc = fetch_taxonomy_doc("subjects")
    subject_options = get_subject_options(subjects_doc, candidate_years, new_program, new_term)
    if not subject_options:
        subject_options = get_subjects_for_program(new_program or new_year, get_year_rule(new_year, 'SUBJECTS_LIST_KEY', 'SUBJECTS_BY_PROGRAM'))
    if not subject_options:
        subject_options = [file_data.get('subject', '')]
    if file_data.get('subject') not in subject_options:
        if file_data.get('subject'):
            subject_options = [file_data.get('subject')] + subject_options
    new_subject = st.selectbox("المادة (جديد)", subject_options, index=subject_options.index(file_data.get('subject')) if file_data.get('subject') in subject_options else 0)

    lectures_doc = fetch_taxonomy_doc("lectures")
    lecture_options = get_lecture_options(lectures_doc, candidate_years, new_program, new_term, new_subject)
    if not lecture_options:
        lecture_options = [file_data.get('lecture', '')]
    if file_data.get('lecture') not in lecture_options:
        if file_data.get('lecture'):
            lecture_options = [file_data.get('lecture')] + lecture_options
    new_lecture = st.selectbox("المحاضرة (جديد)", lecture_options, index=lecture_options.index(file_data.get('lecture')) if file_data.get('lecture') in lecture_options else 0)

    col_save, col_cancel = st.columns(2)
    if col_save.button("💾 حفظ التغييرات"):
        update_payload = {
            'display_name': display_name.strip() or file_data.get('display_name'),
            'year': new_year.strip(),
            'program': new_program.strip(),
            'term': new_term.strip(),
            'subject': new_subject.strip(),
            'lecture': new_lecture.strip()
        }
        try:
            asyncio.run(db_module.update_file_metadata(file_data['id'], update_payload))
            asyncio.run(db_module.update_taxonomy(
                update_payload['program'],
                update_payload['term'],
                update_payload['subject'],
                update_payload['lecture']
            ))
            st.success("تم حفظ التعديلات بنجاح.")
            st.session_state.file_edit_context = None
            st.session_state.manage_files_results = []
            st.rerun()
        except Exception as e:
            st.error(f"فشل في تحديث الملف: {e}")

    if col_cancel.button("إلغاء التعديل"):
        st.session_state.file_edit_context = None
        st.rerun()


def render_delete_confirmation(file_data: dict):
    st.warning(f"هل أنت متأكد أنك تريد حذف '{file_data.get('display_name')}'؟")
    col_confirm, col_cancel = st.columns(2)
    if col_confirm.button("نعم، متأكد", key="confirm_delete"):
        try:
            asyncio.run(db_module.delete_file(file_data['id']))
            st.success("تم حذف الملف بنجاح.")
            st.session_state.manage_files_results = [
                f for f in st.session_state.manage_files_results if f['id'] != file_data['id']
            ]
            st.session_state.file_delete_context = None
            st.rerun()
        except Exception as e:
            st.error(f"فشل في حذف الملف: {e}")
    if col_cancel.button("إلغاء", key="cancel_delete"):
        st.session_state.file_delete_context = None
        st.rerun()

def main():
    """Main dashboard interface with secure authentication."""
    # Load configuration data first
    load_initial_data()
    
    if not st.session_state.authenticated:
        login_form()
        return
        
    # View selector
    st.sidebar.title("لوحة التحكم")
    st.title("لوحة تحكم المشرف - Uploader Bot")
    view = st.sidebar.radio("اختر الصفحة", ["رفع الملفات", "إدارة المواد", "إدارة الملفات"])
    
    # Route to appropriate page
    if view == "إدارة المواد":
        manage_subjects_page()
        return
    if view == "إدارة الملفات":
        manage_files_page()
        return
    
    # Upload page
    st.title("File Upload Dashboard")
    
    # Dynamic selection widgets (OUTSIDE form) - Firebase-driven
    selection = render_taxonomy_selectors()
    selected_year = selection['year']
    selected_program = selection['program']
    selected_term = selection['term']
    selected_subject = selection['subject']
    current_rules = selection.get('rules', {}) or {}
    
    # File upload and mailbox fetch (outside form)
    st.markdown("---")
    uploaded_file = st.file_uploader("1. رفع مباشر للملف (حتى 48MB):", type=None)
    st.markdown("--- **OR** ---")
    col1, col2 = st.columns([3, 1])
    with col2:
        st.write(" ")
        fetch_clicked = st.button("جلب آخر ملف 🚀", use_container_width=True)
    with col1:
        if fetch_clicked:
            try:
                mailbox_data = asyncio.run(db_module.get_last_uploaded_file())
                if mailbox_data:
                    st.session_state.file_id_input = mailbox_data.get('last_uploaded_file_id', '')
                    st.success(f"تم جلب: {mailbox_data.get('last_uploaded_file_name')}")
                if not mailbox_data:
                    st.error("الصندوق فارغ!")
            except Exception as e:
                st.error(f"فشل الجلب: {e}")
        file_id_input = st.text_input("2. أدخل File ID (أو اضغط 'جلب'):", key="file_id_input")
    
    # Separator before form
    st.markdown("---")
    
    # Dual Upload Form (text inputs + submit)
    with st.form("upload_form"):
        display_name = st.text_input("Display Name (اسم العرض)")
        lecture = st.text_input("Lecture (المحاضرة)")
        submit_button = st.form_submit_button("Upload")
    
    # Handle form submission
    if submit_button:
        file_id_value = st.session_state.get('file_id_input', '')
        is_valid, error_msg = validate_file_uploaded(uploaded_file, file_id_value)
        if not is_valid:
            st.error(error_msg)
            return

        required_fields = {
            "Display Name (اسم العرض)": display_name,
            "الفرقة": selected_year,
            "التخصص": selected_program,
            "الترم": selected_term,
            "المادة": selected_subject,
            "المحاضرة": lecture,
        }

        if not current_rules.get('REQUIRES_PROGRAM', True):
            required_fields.pop("التخصص", None)
        if not current_rules.get('REQUIRES_TERM', True):
            required_fields.pop("الترم", None)

        missing_fields = [label for label, value in required_fields.items() if not value]
        if missing_fields:
            st.error("يرجى استكمال الحقول التالية: " + ", ".join(missing_fields))
            return

        try:
            file_data = {
                'display_name': display_name,
                'original_name': uploaded_file.name if uploaded_file else f"{display_name}.file",
                'year': selected_year,
                'program': selected_program if current_rules.get('REQUIRES_PROGRAM', True) else '',
                'term': selected_term if current_rules.get('REQUIRES_TERM', True) else '',
                'subject': selected_subject,
                'lecture': lecture
            }
            
            doc_id = asyncio.run(upload_file(file_data, uploaded_file, file_id_value))
            st.success(f"File uploaded successfully! (ID: {doc_id})")
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
            logging.exception("Upload error")

if __name__ == "__main__":
    main()

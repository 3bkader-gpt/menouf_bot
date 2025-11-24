"""
Main bot application — Refactored with ConversationHandler, Smart Breadcrumbs, and File Cards.

- Uses the DAL (db.py) for Firestore interactions
- Uses ConversationHandler to store navigation state in context.user_data
- Implements Smart Breadcrumbs showing user's current path
- Implements File Cards with rich formatting
- Implements prefix search using name_lower via search_files
"""

import logging
import os
import asyncio
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument
from telegram.helpers import escape_markdown
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    InlineQueryHandler,
    filters
)
from telegram.error import BadRequest

# Database functions
from db import (
    init_firebase,
    get_taxonomy_doc,
    get_files,
    get_file_details,
    search_files,
    set_last_uploaded_file,
)

# Centralized strings
from strings import Strings as S

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHANNEL_ID = os.getenv("TELEGRAM_ADMIN_CHANNEL_ID")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
FIREBASE_KEY_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN not set in environment")
if not TELEGRAM_ADMIN_CHANNEL_ID:
    raise RuntimeError("TELEGRAM_ADMIN_CHANNEL_ID not set in environment")
if not (FIREBASE_KEY_PATH or FIREBASE_KEY_JSON):
    raise RuntimeError("Provide FIREBASE_SERVICE_ACCOUNT_KEY_PATH or FIREBASE_SERVICE_ACCOUNT_JSON in environment")

TELEGRAM_ADMIN_CHANNEL_ID_INT = int(TELEGRAM_ADMIN_CHANNEL_ID)



# ----------------- Conversation States -----------------
SELECT_PROGRAM = 1
SELECT_TERM = 2
SELECT_SUBJECT = 3
SELECT_LECTURE = 4
SELECT_FILE = 5

# Rate limit: 3 reports per user per hour
_report_tracker = defaultdict(list)

# ----------------- Handlers -----------------

WELCOME_PHOTO_ID = "AgACAgQAAxkBAAEf4cppCmtl9VvqkwzS3T8JmXYNFEY-DgACqAtrG2hXWVA8lfmE5ArAbgEAAwIAA3kAAzYE"
WELCOME_PHOTO_URL = "https://i.imgur.com/gjl440T.png"

# ----------------- Handler Factory Pattern -----------------

def create_navigation_handler(
    key_name: str,          # e.g., 'year', 'program'
    next_state: int,
    breadcrumb_template: str,
    prompt: str,
    taxonomy_doc_key: str,  # The key to retrieve the list from (e.g., 'programs', 'terms')
    back_callback_template: str,     # Template for the back button callback
    use_compound_key: bool = False  # Whether to use compound keys like "year_program"
):
    """Factory function to create navigation handlers with shared logic."""
    
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        try:
            # 1. Parse the new selection from callback data
            new_value = query.data.split(":", 1)[1]
            
            # 2. Update state and build path
            if 'path' not in context.user_data:
                context.user_data['path'] = {}
            
            path = context.user_data['path']
            path[key_name] = new_value
            
            # 3. Fetch the next list of options
            taxonomy_doc = await get_taxonomy_doc(taxonomy_doc_key)
            
            # 4. Build the key for taxonomy lookup
            if use_compound_key:
                # Build compound key based on current path
                key_parts = []
                order = ['program', 'term', 'subject']
                for k in order:
                    if k in path:
                        key_parts.append(path[k])
                    if k == key_name:
                        break
                lookup_key = "_".join(key_parts)
            else:
                # Simple key lookup
                lookup_key = new_value
            
            options = resolve_taxonomy_options(taxonomy_doc, lookup_key)
            
            # 5. Build keyboard
            keyboard = []
            # Map taxonomy keys to callback prefixes
            callback_map = {
                S.TAX_DOC_PROGRAMS: "program",
                S.TAX_DOC_TERMS: "term", 
                S.TAX_DOC_SUBJECTS: "subject",
                S.TAX_DOC_LECTURES: "lecture"
            }
            prefix = callback_map.get(taxonomy_doc_key, "item")
            
            for option in sorted(options):
                keyboard.append([InlineKeyboardButton(option, callback_data=f"{prefix}:{option}")])
            
            # Build dynamic back callback
            if "{" in back_callback_template:
                back_callback = back_callback_template.format(**path)
            else:
                back_callback = back_callback_template
            
            # Add navigation buttons
            keyboard.append([
                InlineKeyboardButton(S.BTN_BACK, callback_data=back_callback),
                InlineKeyboardButton(S.BTN_MAIN_MENU, callback_data="main_menu")
            ])
            
            # 6. Build breadcrumb text
            text = breadcrumb_template.format(**path, prompt=prompt)
            
            # 7. Send response
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return next_state
            
        except (KeyError, ValueError) as e:
            logging.error(f"Error in {key_name}_handler: {e}")
            await query.edit_message_text(
                S.GENERIC_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(S.BTN_MAIN_MENU, callback_data="main_menu")]
                ])
            )
            return SELECT_PROGRAM
    
    return handler


def extract_program_list(doc: dict) -> list:
    """Support both legacy year-based doc and new program-centric format."""
    if not isinstance(doc, dict):
        return []
    programs = []
    base = doc.get('list')
    if isinstance(base, list):
        programs.extend(base)
    for key, value in doc.items():
        if key == 'list':
            continue
        if isinstance(value, list):
            programs.extend(value)
    deduped = []
    seen = set()
    for program in programs:
        if not program or program in seen:
            continue
        seen.add(program)
        deduped.append(program)
    return deduped


def resolve_taxonomy_options(doc: dict, lookup_key: str) -> list[str]:
    """Return options for both new program-centric keys and legacy year-prefixed keys."""
    if not isinstance(doc, dict) or not lookup_key:
        return []
    options: list[str] = []
    direct = doc.get(lookup_key)
    if isinstance(direct, list):
        options.extend(direct)
    suffix = f"_{lookup_key}"
    for key, value in doc.items():
        if key == lookup_key or not isinstance(value, list):
            continue
        if key.endswith(suffix):
            options.extend(value)
    return sorted({opt for opt in options if opt})

async def show_programs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Render the top-level program selection menu - Program-Centric."""
    query = update.callback_query
    if query:
        await query.answer()
        target_message = query.message
    else:
        target_message = update.message

    context.user_data['path'] = {}

    taxonomy = await get_taxonomy_doc(S.TAX_DOC_PROGRAMS)
    programs = extract_program_list(taxonomy)

    if not programs and target_message:
        await target_message.reply_text(
            S.NO_YEARS_AVAILABLE,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(S.BTN_MAIN_MENU, callback_data="main_menu")]
            ])
        )
        return SELECT_PROGRAM

    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"program:{option}")]
        for option in programs
    ]
    keyboard.append([InlineKeyboardButton(S.SEARCH, callback_data="search_start")])

    prompt = "اختر القسم/التخصص"
    if query:
        await query.edit_message_text(
            prompt,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif target_message:
        await target_message.reply_text(
            prompt,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return SELECT_PROGRAM

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler: sends a welcome photo with main menu buttons.
    """
    # Clear user data to start fresh
    context.user_data.clear()
    return await show_programs_menu(update, context)


async def lecture_selected_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show files with File Cards."""
    query = update.callback_query
    await query.answer()
    
    try:
        lecture = query.data.split(":", 1)[1]
        path = context.user_data['path']
        program = path['program']
        term = path['term']
        subject = path['subject']
        path['lecture'] = lecture
        
        files = await get_files(program, term, subject, lecture)
        
        # Build breadcrumb text
        breadcrumb_text = S.BREADCRUMB_LECTURE.format(program=path['program'], term=path['term'], subject=path['subject'], lecture=path['lecture'])
        
        if not files:
            keyboard = [[
                InlineKeyboardButton(S.BTN_BACK, callback_data=f"subject:{subject}"),
                InlineKeyboardButton(S.BTN_MAIN_MENU, callback_data="main_menu")
            ]]
            await query.edit_message_text(
                text=breadcrumb_text + S.NO_FILES_AVAILABLE,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return SELECT_FILE
        
        # Build file cards text
        cards_text = ""
        keyboard = []
        
        for i, file in enumerate(files):
            # Get file extension/type
            file_ext = file.get('file_type', 'FILE')
            
            # Add card to text
            cards_text += (
                f"\n---\n"
                f"**{i+1}️⃣ {file['display_name']}** `[{file_ext}]`\n"
            )
            
            # Create a new row for each file with Download and Report buttons
            button_row = [
                InlineKeyboardButton(
                    S.DOWNLOAD_FILE.format(number=i+1),
                    callback_data=f"file:{file['id']}"
                ),
                InlineKeyboardButton(
                    S.REPORT_PROBLEM,
                    callback_data=f"report:{file['id']}"
                )
            ]
            keyboard.append(button_row)
        
        # Add Back + Main Menu buttons on their own row
        keyboard.append([
            InlineKeyboardButton(S.BTN_BACK, callback_data=f"subject:{subject}"),
            InlineKeyboardButton(S.BTN_MAIN_MENU, callback_data="main_menu")
        ])
        
        # Combine breadcrumb and cards
        text = breadcrumb_text + S.FILES_AVAILABLE + cards_text
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return SELECT_FILE
        
    except KeyError as e:
        logging.error(f"Error in lecture_selected_handler: {e}")
        await query.edit_message_text(
            S.GENERIC_ERROR,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(S.BTN_MAIN_MENU, callback_data="main_menu")]
            ])
        )
        return SELECT_PROGRAM


async def file_selected_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file selection using Firestore doc_id"""
    query = update.callback_query
    await query.answer()
    
    doc_id = query.data.split(':')[1]
    
    try:
        file_data = await get_file_details(doc_id)
        
        if not file_data:
            await query.edit_message_text(S.FILE_NOT_FOUND)
            return SELECT_FILE
            
        telegram_file_id = file_data.get('file_id')
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=telegram_file_id,
            filename=file_data.get('display_name')
        )
        
        return SELECT_FILE
        
    except BadRequest as e:
        if "file_id" in str(e).lower():
            await query.edit_message_text(
                S.FILE_ERROR
            )
            logging.error(f"Invalid file_id for doc {doc_id}")
            return SELECT_FILE


async def search_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to send search text."""
    keyboard = [[InlineKeyboardButton(S.BTN_BACK_TO_MAIN, callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.delete()
        await query.message.reply_text(
            S.SEARCH_PROMPT,
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            S.SEARCH_PROMPT,
            reply_markup=reply_markup
        )


async def handle_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catch text messages as search queries."""
    if not update.message or not update.message.text:
        return

    query_text = update.message.text.strip()
    results = await search_files(query_text)
    if not results:
        await update.message.reply_text(S.SEARCH_NO_RESULTS)
        return

    await update.message.reply_text(S.SEARCH_RESULTS.format(query=query_text))

    keyboard = []
    for f in results:
        keyboard.append([InlineKeyboardButton(f["display_name"], callback_data=f"file:{f['id']}")])
    keyboard.append([InlineKeyboardButton(S.MAIN_MENU, callback_data="main_menu")])
    await update.message.reply_text("", reply_markup=InlineKeyboardMarkup(keyboard))


async def mailbox_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Listens to the admin channel and saves file_ids to the mailbox."""
    message = update.effective_message
    if not message or message.chat_id != TELEGRAM_ADMIN_CHANNEL_ID_INT:
        return

    file = message.document or message.video or message.audio
    if not file:
        return

    file_id = file.file_id
    original_name = getattr(file, "file_name", None) or "N/A"

    await set_last_uploaded_file(file_id, original_name)

    try:
        await message.reply_text(
            "✅ **File ID Mailbox Updated**\n"
            f"`{file_id}`\n\n"
            "(Ready to be fetched in Dashboard)",
            parse_mode="MarkdownV2"
        )
    except Exception:
        # Fail silently if replying isn't allowed
        pass


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    if query:
        await query.answer()
        context.user_data.clear()
        return await show_programs_menu(update, context)


async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler for unknown callbacks."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            S.UNKNOWN_BUTTON, 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(S.MAIN_MENU, callback_data="main_menu")]])
        )
        return SELECT_PROGRAM


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query. This is called when a user types @YourBotName"""
    query = update.inline_query.query
    
    # Don't show results for an empty query
    if not query or len(query) < 3:  # Only search if 3+ chars
        await update.inline_query.answer([], cache_time=10)
        return
    
    # Get results from our database
    files = await search_files(query)
    
    results = []
    for file in files:
        # Check if we have the necessary data
        if 'file_id' in file and 'display_name' in file:
            results.append(
                InlineQueryResultCachedDocument(
                    id=str(uuid.uuid4()),  # Must be a unique string
                    title=file['display_name'],
                    document_file_id=file['file_id'],  # The file_id of the file on Telegram servers
                    caption=S.INLINE_FILE_CAPTION.format(file_name=file['display_name'])
                )
            )
    
    # Answer the inline query
    await update.inline_query.answer(results, cache_time=10)


async def report_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle file report button clicks."""
    query = update.callback_query
    user_id = query.from_user.id
    doc_id = query.data.split(":", 1)[1]
    now = datetime.now()
    
    try:
        # --- Start of New Rate Limit Logic ---
        
        # 1. Clean old reports (> 1 hour ago) for this user
        _report_tracker[user_id] = [
            ts for ts in _report_tracker[user_id]
            if now - ts < timedelta(hours=1)
        ]
        
        # 2. Check rate limit
        if len(_report_tracker[user_id]) >= 3:
            await query.answer(
                S.RATE_LIMIT_EXCEEDED,
                show_alert=True
            )
            logging.warning(f"Rate limit hit for user {user_id} reporting doc {doc_id}")
            return  # Stop execution
        
        # 3. If limit is okay, record this new report
        _report_tracker[user_id].append(now)
        
        # --- End of New Rate Limit Logic ---
        # 4. Notify the user (original logic)
        await query.answer(S.REPORT_SUCCESS, show_alert=True)
        
        # 5. Get file details to send to admin (original logic)
        file_details = await get_file_details(doc_id)
        
        # 6. Clean (escape) variables for MarkdownV2
        file_name = escape_markdown(file_details.get('display_name', 'N/A'), version=2)
        clean_doc_id = escape_markdown(doc_id, version=2)
        user_name = escape_markdown(query.from_user.full_name, version=2)
        
        user_username = query.from_user.username
        if user_username:
            user_mention = escape_markdown(f"(@{user_username})", version=2)
        else:
            user_mention = "(No username)"
        
        # 7. Log the report for manual review (no channel notification required)
        alert_text = S.REPORT_ADMIN_ALERT.format(
            file_name=file_name,
            doc_id=clean_doc_id,
            user_name=user_name,
            user_mention=user_mention
        )
        logging.info("Report received: %s", alert_text)
    except Exception as e:
        logging.error(f"Error in report_file_handler: {e}")
        await query.answer(S.REPORT_ERROR, show_alert=True)


# ----------------- Application setup -----------------

def register_handlers(app):
    # Create reusable navigation handlers using the factory pattern
    program_handler = create_navigation_handler(
        key_name='program',
        next_state=SELECT_TERM,
        breadcrumb_template=S.BREADCRUMB_PROGRAM,
        prompt=S.SELECT_TERM,
        taxonomy_doc_key=S.TAX_DOC_TERMS,
        back_callback_template="main_menu",
        use_compound_key=True
    )

    term_handler = create_navigation_handler(
        key_name='term',
        next_state=SELECT_SUBJECT,
        breadcrumb_template=S.BREADCRUMB_TERM,
        prompt=S.SELECT_SUBJECT,
        taxonomy_doc_key=S.TAX_DOC_SUBJECTS,
        back_callback_template="program:{program}",
        use_compound_key=True
    )

    subject_handler = create_navigation_handler(
        key_name='subject',
        next_state=SELECT_LECTURE,
        breadcrumb_template=S.BREADCRUMB_SUBJECT,
        prompt=S.SELECT_LECTURE,
        taxonomy_doc_key=S.TAX_DOC_LECTURES,
        back_callback_template="term:{term}",
        use_compound_key=True
    )

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(main_menu_handler, pattern="^main_menu$")
        ],
        states={
            SELECT_PROGRAM: [
                CallbackQueryHandler(program_handler, pattern="^program:"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SELECT_TERM: [
                CallbackQueryHandler(term_handler, pattern="^term:"),
                CallbackQueryHandler(program_handler, pattern="^program:"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SELECT_SUBJECT: [
                CallbackQueryHandler(subject_handler, pattern="^subject:"),
                CallbackQueryHandler(term_handler, pattern="^term:"),
                CallbackQueryHandler(program_handler, pattern="^program:"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SELECT_LECTURE: [
                CallbackQueryHandler(lecture_selected_handler, pattern="^lecture:"),
                CallbackQueryHandler(subject_handler, pattern="^subject:"),
                CallbackQueryHandler(term_handler, pattern="^term:"),
                CallbackQueryHandler(program_handler, pattern="^program:"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
            SELECT_FILE: [
                CallbackQueryHandler(file_selected_handler, pattern="^file:"),
                CallbackQueryHandler(lecture_selected_handler, pattern="^lecture:"),
                CallbackQueryHandler(subject_handler, pattern="^subject:"),
                CallbackQueryHandler(term_handler, pattern="^term:"),
                CallbackQueryHandler(program_handler, pattern="^program:"),
                CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"),
            CallbackQueryHandler(unknown_callback),
        ],
        per_user=True,
        per_chat=True,
    )
    
    # Add global handlers BEFORE conversation handler so they're checked first
    app.add_handler(CallbackQueryHandler(report_file_handler, pattern="^report:"))
    app.add_handler(CallbackQueryHandler(search_start_handler, pattern="^search_start$"))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.VIDEO | filters.AUDIO) & filters.Chat(chat_id=TELEGRAM_ADMIN_CHANNEL_ID_INT),
        mailbox_handler
    ))
    
    # Add conversation handler
    app.add_handler(conv_handler)
    
    # Add text search handler (must be after conversation handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_search))


def main() -> None:
init_firebase(FIREBASE_KEY_PATH, FIREBASE_KEY_JSON)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    register_handlers(app)
    print("Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

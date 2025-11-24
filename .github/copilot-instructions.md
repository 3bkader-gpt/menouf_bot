github# Uploader Bot Project Guidelines

## Architecture Overview
This project is a Telegram bot for managing and sharing academic files, built with:
- `python-telegram-bot` for the bot interface
- Firebase/Firestore for data storage
- Streamlit for the admin dashboard

### Key Components
1. `bot.py`: Main bot application
   - Handles user interactions using command/callback handlers
   - Implements hierarchical navigation (Year → Program → Term → Subject → Files)
   - Provides search functionality and file rating system

2. `db.py`: Data Access Layer (DAL)
   - Manages Firebase/Firestore interactions
   - Uses async/await pattern with `asyncio.to_thread` for non-blocking operations
   - Key collections: `files` (file metadata) and `ratings` (user feedback)

3. `dashboard.py`: Admin interface
   - Streamlit-based file upload interface
   - Handles file staging through Telegram admin channel
   - Password-protected admin access

## Project Conventions

### Asynchronous Programming
- All database operations are wrapped in `asyncio.to_thread()` to prevent blocking
- Bot handlers are async coroutines using `async/await`
- Example pattern:
```python
async def get_files(year: str, program: str, term: str, subject: str):
    snaps = await asyncio.to_thread(_query_files_by_filters_blocking, year, program, term, subject)
    # Process results...
```

### File Document Structure
```python
{
    "display_name": str,       # User-friendly name
    "name_lower": str,         # Lowercase name for search
    "original_name": str,      # Original filename
    "file_id": str,           # Telegram file_id
    "year": str,
    "program": str,
    "term": str,
    "subject": str,
    "created_at": timestamp
}
```

### Environment Setup
Required environment variables (.env):
```
TELEGRAM_TOKEN=<bot_token>
TELEGRAM_ADMIN_CHANNEL_ID=<channel_id>
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=<path>
ADMIN_PASSWORD=<dashboard_password>
```

## Development Workflows

### Adding New Bot Commands
1. Create async handler function in `bot.py`
2. Register in `register_handlers()` with appropriate pattern
3. Update callback data patterns if needed
Example:
```python
async def new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Handler logic...

app.add_handler(CallbackQueryHandler(new_handler, pattern="^pattern:"))
```

### File Upload Flow
1. Admin uploads file through Streamlit dashboard
2. File sent to admin channel to obtain `file_id`
3. Metadata saved to Firestore with `file_id`
4. Bot retrieves `file_id` to serve file to users

## Testing & Debugging
- Run bot locally: `python bot.py`
- Launch admin dashboard: `streamlit run dashboard.py`
- Monitor admin channel for file upload messages
- Check Firestore console for document structure

## Localization
- User-facing strings are in Arabic (RTL)
- String constants defined at top of `bot.py`
- Keep Arabic strings consistent with existing UI patterns
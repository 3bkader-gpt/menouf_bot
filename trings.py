[1mdiff --git a/bot.py b/bot.py[m
[1mindex ff9efbf..5539257 100644[m
[1m--- a/bot.py[m
[1m+++ b/bot.py[m
[36m@@ -78,10 +78,9 @@[m [mTELEGRAM_ADMIN_CHANNEL_ID_INT = int(TELEGRAM_ADMIN_CHANNEL_ID)[m
 [m
 # ----------------- Conversation States -----------------[m
 SELECT_PROGRAM = 1[m
[31m-SELECT_TERM = 2[m
[31m-SELECT_SUBJECT = 3[m
[31m-SELECT_LECTURE = 4[m
[31m-SELECT_FILE = 5[m
[32m+[m[32mSELECT_SUBJECT = 2[m
[32m+[m[32mSELECT_LECTURE = 3[m
[32m+[m[32mSELECT_FILE = 4[m
 [m
 # Rate limit: 3 reports per user per hour[m
 _report_tracker = defaultdict(list)[m
[36m@@ -94,13 +93,13 @@[m [mWELCOME_PHOTO_URL = "https://i.imgur.com/gjl440T.png"[m
 # ----------------- Handler Factory Pattern -----------------[m
 [m
 def create_navigation_handler([m
[31m-    key_name: str,          # e.g., 'year', 'program'[m
[32m+[m[32m    key_name: str,          # e.g., 'program', 'subject'[m
     next_state: int,[m
     breadcrumb_template: str,[m
     prompt: str,[m
[31m-    taxonomy_doc_key: str,  # The key to retrieve the list from (e.g., 'programs', 'terms')[m
[32m+[m[32m    taxonomy_doc_key: str,  # The key to retrieve the list from (e.g., 'subjects', 'lectures')[m
     back_callback_template: str,     # Template for the back button callback[m
[31m-    use_compound_key: bool = False  # Whether to use compound keys like "year_program"[m
[32m+[m[32m    use_compound_key: bool = False  # Whether to use compound keys like "program_subject"[m
 ):[m
     """Factory function to create navigation handlers with shared logic."""[m
     [m
[36m@@ -124,9 +123,9 @@[m [mdef create_navigation_handler([m
             [m
             # 4. Build the key for taxonomy lookup[m
             if use_compound_key:[m
[31m-                # Build compound key based on current path[m
[32m+[m[32m                # Build compound key based on current path (without term)[m
                 key_parts = [][m
[31m-                order = ['program', 'term', 'subject'][m
[32m+[m[32m                order = ['program', 'subject'][m
                 for k in order:[m
                     if k in path:[m
                         key_parts.append(path[k])[m
[36m@@ -144,7 +143,6 @@[m [mdef create_navigation_handler([m
             # Map taxonomy keys to callback prefixes[m
             callback_map = {[m
                 S.TAX_DOC_PROGRAMS: "program",[m
[31m-                S.TAX_DOC_TERMS: "term", [m
                 S.TAX_DOC_SUBJECTS: "subject",[m
                 S.TAX_DOC_LECTURES: "lecture"[m
             }[m
[36m@@ -285,7 +283,7 @@[m [masync def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):[m
 [m
 [m
 async def lecture_selected_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):[m
[31m-    """Show files with File Cards."""[m
[32m+[m[32m    """Show files with File Cards - fetches from all terms."""[m
     query = update.callback_query[m
     await query.answer()[m
     [m
[36m@@ -293,14 +291,34 @@[m [masync def lecture_selected_handler(update: Update, context: ContextTypes.DEFAULT[m
         lecture = query.data.split(":", 1)[1][m
         path = context.user_data['path'][m
         program = path['program'][m
[31m-        term = path['term'][m
         subject = path['subject'][m
         path['lecture'] = lecture[m
     [m
[31m-        files = await get_files(program, term, subject, lecture)[m
[32m+[m[32m        # Query files without term filter - get from all terms[m
[32m+[m[32m        query_ref = db.collection('files').where(filter=FieldFilter('program', '==', program)).where(filter=FieldFilter('subject', '==', subject)).where(filter=FieldFilter('lecture', '==', lecture))[m
[32m+[m[32m        docs = await asyncio.to_thread(query_ref.get)[m
[32m+[m[41m        [m
[32m+[m[32m        files = [][m
[32m+[m[32m        for doc in docs:[m
[32m+[m[32m            data = doc.to_dict()[m
[32m+[m[32m            if not data.get('file_id'):[m
[32m+[m[32m                continue[m
[32m+[m[32m            original_name = data.get('original_name', 'file.unknown')[m
[32m+[m[32m            if '.' in original_name:[m
[32m+[m[32m                file_type = original_name.split('.')[-1].upper()[m
[32m+[m[32m            else:[m
[32m+[m[32m                file_type = 'FILE'[m
[32m+[m[41m            [m
[32m+[m[32m            files.append({[m
[32m+[m[32m                'display_name': data.get('display_name') or 'ملف',[m
[32m+[m[32m                'file_id': data.get('file_id'),[m
[32m+[m[32m                'id': doc.id,[m
[32m+[m[32m                'original_name': original_name,[m
[32m+[m[32m                'file_type': file_type[m
[32m+[m[32m            })[m
         [m
         # Build breadcrumb text[m
[31m-        breadcrumb_text = S.BREADCRUMB_LECTURE.format(program=path['program'], term=path['term'], subject=path['subject'], lecture=path['lecture'])[m
[32m+[m[32m        breadcrumb_text = S.BREADCRUMB_LECTURE.format(program=path['program'], subject=path['subject'], lecture=path['lecture'])[m
         [m
         if not files:[m
             keyboard = [[[m
[36m@@ -498,7 +516,7 @@[m [masync def subject_search_handler(update: Update, context: ContextTypes.DEFAULT_T[m
 [m
 [m
 async def program_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):[m
[31m-    """Handle program selection for a subject - show terms."""[m
[32m+[m[32m    """Handle program selection for a subject - show lectures directly."""[m
     query = update.callback_query[m
     await query.answer()[m
     [m
[36m@@ -508,27 +526,73 @@[m [masync def program_subject_handler(update: Update, context: ContextTypes.DEFAULT_[m
     [m
     context.user_data['path'] = {'program': program, 'subject': subject}[m
     [m
[31m-    # Get terms for this program[m
[31m-    terms_doc = await get_taxonomy_doc(S.TAX_DOC_TERMS)[m
[31m-    terms = resolve_taxonomy_options(terms_doc, program)[m
[32m+[m[32m    # Get lectures for this program/subject (from all terms)[m
[32m+[m[32m    lectures_doc = await get_taxonomy_doc(S.TAX_DOC_LECTURES)[m
[32m+[m[41m    [m
[32m+[m[32m    # Try to find lectures with different key patterns[m
[32m+[m[32m    lectures = set()[m
[32m+[m[32m    for key, values in lectures_doc.items():[m
[32m+[m[32m        if isinstance(values, list) and subject in key and program in key:[m
[32m+[m[32m            lectures.update(values)[m
     [m
[31m-    if not terms:[m
[31m-        # Fallback to default terms[m
[31m-        terms = ["اول", "تاني"][m
[32m+[m[32m    if not lectures:[m
[32m+[m[32m        # Try to get files directly (without lecture filter)[m
[32m+[m[32m        try:[m
[32m+[m[32m            query_ref = db.collection('files').where(filter=FieldFilter('program', '==', program)).where(filter=FieldFilter('subject', '==', subject))[m
[32m+[m[32m            docs = await asyncio.to_thread(query_ref.get)[m
[32m+[m[32m            files = [{'id': doc.id, 'display_name': doc.get('display_name') or doc.get('original_name') or "ملف", 'file_id': doc.get('file_id'), 'file_type': 'FILE'} for doc in docs if doc.get('file_id')][m
[32m+[m[41m            [m
[32m+[m[32m            if files:[m
[32m+[m[32m                # Show files directly[m
[32m+[m[32m                context.user_data['path']['lecture'] = ""[m
[32m+[m[32m                breadcrumb_text = S.BREADCRUMB_LECTURE.format(program=program, subject=subject, lecture="")[m
[32m+[m[32m                cards_text = ""[m
[32m+[m[32m                keyboard = [][m
[32m+[m[41m                [m
[32m+[m[32m                for i, file in enumerate(files):[m
[32m+[m[32m                    file_ext = file.get('file_type', 'FILE')[m
[32m+[m[32m                    cards_text += f"\n---\n**{i+1}️⃣ {file['display_name']}** `[{file_ext}]`\n"[m
[32m+[m[32m                    button_row = [[m
[32m+[m[32m                        InlineKeyboardButton(S.DOWNLOAD_FILE.format(number=i+1), callba
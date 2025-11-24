#!/usr/bin/env python3
"""
Migrate Firebase taxonomy from Year-Based to Program-Centric structure
"""
import asyncio
import os
from dotenv import load_dotenv
from firebase_admin import firestore

# Import our db module
from db import init_firebase

load_dotenv()

async def migrate_taxonomy():
    print('🚀 Starting Firebase Migration: Year-Based → Program-Centric\n')

    # Initialize Firebase
    firebase_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    firebase_key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not (firebase_key_path or firebase_key_json):
        print("❌ ERROR: Provide FIREBASE_SERVICE_ACCOUNT_KEY_PATH or FIREBASE_SERVICE_ACCOUNT_JSON in .env")
        return

    init_firebase(firebase_key_path, firebase_key_json)
    db = firestore.client()
    print("✅ Firebase initialized\n")

    # Get current data
    print("📖 Reading current taxonomy data...")
    programs_ref = db.collection('taxonomy').document('programs')
    terms_ref = db.collection('taxonomy').document('terms')
    subjects_ref = db.collection('taxonomy').document('subjects')
    lectures_ref = db.collection('taxonomy').document('lectures')

    programs_doc = programs_ref.get().to_dict() or {}
    terms_doc = terms_ref.get().to_dict() or {}
    subjects_doc = subjects_ref.get().to_dict() or {}
    lectures_doc = lectures_ref.get().to_dict() or {}

    print("Current Programs:", programs_doc)
    print("Current Terms:", terms_doc)
    print("Current Subjects:", subjects_doc)
    print("Current Lectures:", lectures_doc)
    print()

    # Migration logic
    new_programs = {'list': []}
    new_terms = {}
    new_subjects = {}
    new_lectures = {}

    # Extract programs from old structure
    # Old: {"تانيه": ["حاسبات", "تحكم", "اتصالات"]}
    # New: {"list": ["حاسبات", "تحكم", "اتصالات"]}
    if programs_doc:
        for year, programs_list in programs_doc.items():
            if isinstance(programs_list, list):
                new_programs['list'].extend(programs_list)

        # Remove duplicates
        new_programs['list'] = list(set(new_programs['list']))

    print("✅ New Programs structure:", new_programs)

    # Migrate terms
    # Old: {"تانيه_حاسبات": ["اول", "تاني"]}
    # New: {"حاسبات": ["اول", "تاني"]}
    if terms_doc:
        for old_key, terms_list in terms_doc.items():
            if '_' in old_key and old_key.count('_') >= 1:
                # Extract program from "تانيه_حاسبات" → "حاسبات"
                parts = old_key.split('_', 1)  # Split on first underscore
                if len(parts) >= 2:
                    program = parts[1]  # Get program part
                    new_terms[program] = terms_list

    print("✅ New Terms structure:", new_terms)

    # Migrate subjects
    # Old: {"تانيه_حاسبات_اول": ["معالجات", "OOP"]}
    # New: {"حاسبات_اول": ["معالجات", "OOP"]}
    if subjects_doc:
        for old_key, subjects_list in subjects_doc.items():
            if '_' in old_key and old_key.count('_') >= 2:
                # Extract "program_term" from "تانيه_حاسبات_اول" → "حاسبات_اول"
                parts = old_key.split('_', 2)  # Split on first two underscores
                if len(parts) >= 3:
                    program_term = f"{parts[1]}_{parts[2]}"
                    new_subjects[program_term] = subjects_list

    print("✅ New Subjects structure:", new_subjects)

    # Migrate lectures
    # Old: {"تانيه_حاسبات_اول_معالجات": ["محاضرة 1", "محاضرة 2"]}
    # New: {"حاسبات_اول_معالجات": ["محاضرة 1", "محاضرة 2"]}
    if lectures_doc:
        for old_key, lectures_list in lectures_doc.items():
            if '_' in old_key and old_key.count('_') >= 3:
                # Extract "program_term_subject" from "تانيه_حاسبات_اول_معالجات" → "حاسبات_اول_معالجات"
                parts = old_key.split('_', 3)  # Split on first three underscores
                if len(parts) >= 4:
                    program_term_subject = f"{parts[1]}_{parts[2]}_{parts[3]}"
                    new_lectures[program_term_subject] = lectures_list

    print("✅ New Lectures structure:", new_lectures)

    # Confirm migration (auto-confirm for this run)
    print("\n🔄 Ready to migrate. Continuing automatically...")

    # Apply migration
    print("\n📝 Applying migration...")

    # Update programs
    await asyncio.to_thread(programs_ref.set, new_programs)
    print("✅ Programs migrated")

    # Update terms
    await asyncio.to_thread(terms_ref.set, new_terms)
    print("✅ Terms migrated")

    # Update subjects
    await asyncio.to_thread(subjects_ref.set, new_subjects)
    print("✅ Subjects migrated")

    # Update lectures
    await asyncio.to_thread(lectures_ref.set, new_lectures)
    print("✅ Lectures migrated")

    print("\n🎉 Migration completed successfully!")
    print("🔄 You can now restart the bot and dashboard.")

if __name__ == "__main__":
    asyncio.run(migrate_taxonomy())

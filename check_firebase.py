#!/usr/bin/env python3
"""
Check current Firebase taxonomy structure
"""
import asyncio
import os
from dotenv import load_dotenv

# Import our db module
from db import init_firebase, get_taxonomy_doc

load_dotenv()

async def check_current_structure():
    print('=== Checking Current Firebase Structure ===\n')

    # Initialize Firebase
    firebase_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    firebase_key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not (firebase_key_path or firebase_key_json):
        print("ERROR: Provide FIREBASE_SERVICE_ACCOUNT_KEY_PATH or FIREBASE_SERVICE_ACCOUNT_JSON in .env")
        return

    init_firebase(firebase_key_path, firebase_key_json)
    print("✅ Firebase initialized\n")

    # Check programs
    print("📋 Programs:")
    programs_doc = await get_taxonomy_doc('programs')
    print(f"   {programs_doc}\n")

    # Check terms
    print("📋 Terms:")
    terms_doc = await get_taxonomy_doc('terms')
    print(f"   {terms_doc}\n")

    # Check subjects
    print("📋 Subjects:")
    subjects_doc = await get_taxonomy_doc('subjects')
    print(f"   {subjects_doc}\n")

    # Check lectures
    print("📋 Lectures:")
    lectures_doc = await get_taxonomy_doc('lectures')
    print(f"   {lectures_doc}\n")

    print("=== Analysis ===")

    # Check if programs has 'list' key (new format)
    if 'list' in programs_doc:
        print("✅ Programs: Using NEW Program-Centric format")
    elif programs_doc and any('تانيه' in str(k) for k in programs_doc.keys()):
        print("⚠️  Programs: Using OLD Year-Based format")
    else:
        print("❌ Programs: No data found")

    # Check terms structure
    if terms_doc:
        sample_key = next(iter(terms_doc.keys()), '')
        if sample_key.count('_') == 1 and not sample_key.startswith('تانيه'):
            print("✅ Terms: Using NEW Program-Centric format")
        elif any('تانيه_' in key for key in terms_doc.keys()):
            print("⚠️  Terms: Using OLD Year-Based format")
        else:
            print("❓ Terms: Unknown format")

if __name__ == "__main__":
    asyncio.run(check_current_structure())

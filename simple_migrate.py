#!/usr/bin/env python3
"""
Simple Firebase Migration Script - Year-Based to Program-Centric
"""
import asyncio
import os
from firebase_admin import firestore
from db import init_firebase
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    print('🚀 Starting Simple Firebase Migration...\n')

    # Initialize Firebase
    firebase_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    firebase_key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    init_firebase(firebase_key_path, firebase_key_json)
    db = firestore.client()

    print('✅ Firebase initialized')

    # Migration data (based on what we saw earlier)
    new_programs = {
        'list': ['كهرباء', 'حاسبات', 'تحكم']
    }

    new_terms = {
        'كهرباء': ['الاول'],
        'حاسبات': ['تاني'],
        'تحكم': ['اول']
    }

    new_subjects = {
        'كهرباء_الاول': ['فيزياء'],
        'تحكم_اول': ['أساسيات هندسة التحكم'],
        'حاسبات_تاني': ['oop']
    }

    new_lectures = {
        'حاسبات_تاني_oop': ['التالته'],
        'تحكم_اول_أساسيات هندسة التحكم': []
    }

    print('📝 Applying migration...')

    # Update each collection
    await asyncio.to_thread(
        db.collection('taxonomy').document('programs').set,
        new_programs
    )
    print('✅ Programs updated')

    await asyncio.to_thread(
        db.collection('taxonomy').document('terms').set,
        new_terms
    )
    print('✅ Terms updated')

    await asyncio.to_thread(
        db.collection('taxonomy').document('subjects').set,
        new_subjects
    )
    print('✅ Subjects updated')

    await asyncio.to_thread(
        db.collection('taxonomy').document('lectures').set,
        new_lectures
    )
    print('✅ Lectures updated')

    print('\n🎉 Migration completed successfully!')
    print('🔄 You can now restart the bot and dashboard.')

if __name__ == "__main__":
    asyncio.run(migrate())

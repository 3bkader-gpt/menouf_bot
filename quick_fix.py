import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase
firebase_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
firebase_key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if firebase_key_json and not firebase_key_path:
    cred = credentials.Certificate(json.loads(firebase_key_json))
elif firebase_key_path:
    cred = credentials.Certificate(firebase_key_path)
else:
    raise RuntimeError("Provide FIREBASE_SERVICE_ACCOUNT_KEY_PATH or FIREBASE_SERVICE_ACCOUNT_JSON")
firebase_admin.initialize_app(cred)
db = firestore.client()

print("✅ Firebase connected")

# New Program-Centric data
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

# Update Firebase
db.collection('taxonomy').document('programs').set(new_programs)
print("✅ Programs updated")

db.collection('taxonomy').document('terms').set(new_terms)
print("✅ Terms updated")

db.collection('taxonomy').document('subjects').set(new_subjects)
print("✅ Subjects updated")

db.collection('taxonomy').document('lectures').set(new_lectures)
print("✅ Lectures updated")

print("\n🎉 Migration completed! Restart bot and dashboard.")

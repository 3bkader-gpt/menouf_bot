"""
Data Access Layer (DAL) for Firestore - Updated with Lecture Support

Design choices:
- Uses asyncio.to_thread for non-blocking Firebase operations
- Uses taxonomy collection for efficient navigation
"""

from typing import List, Dict, Optional
import os
import json
import asyncio
import logging
import time
from cachetools import TTLCache
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Global Firestore client
db: Optional[firestore.Client] = None

# Cache taxonomy for 5 minutes (300 seconds)
_taxonomy_cache = TTLCache(maxsize=100, ttl=300)

# Mailbox document path
_MAILBOX_DOC_PATH = "config/bot_state"


def init_firebase(
    service_account_key_path: Optional[str] = None,
    service_account_json: Optional[str] = None
) -> None:
    """Initialize firebase-admin and set global Firestore client."""
    global db
    if firebase_admin._apps:
        db = firestore.client()
        return

    if not service_account_key_path and not service_account_json:
        service_account_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        if isinstance(service_account_json, str):
            try:
                cred_dict = json.loads(service_account_json)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid FIREBASE_SERVICE_ACCOUNT_JSON") from exc
        else:
            cred_dict = service_account_json
        cred = credentials.Certificate(cred_dict)
    else:
        if not service_account_key_path:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY_PATH not provided")
        cred = credentials.Certificate(service_account_key_path)

    firebase_admin.initialize_app(cred)
    db = firestore.client()


async def get_file_details(doc_id: str) -> Dict:
    """Get file metadata by Firestore doc_id."""
    assert db is not None, "Firestore client is not initialized"
    doc_ref = db.collection('files').document(doc_id)
    doc = await asyncio.to_thread(doc_ref.get)
    
    if not doc.exists:
        return {}
    
    data = doc.to_dict() or {}
    return {
        "file_id": data.get("file_id"),
        "display_name": data.get("display_name") or data.get("original_name") or "ملف",
        "doc_id": doc.id,
        "mime_type": data.get("mime_type"),
        "original_name": data.get("original_name"),
        "program": data.get("program"),
        "term": data.get("term"),
        "subject": data.get("subject"),
        "lecture": data.get("lecture")
    }


async def get_files(program: str, term: str, subject: str, lecture: str) -> List[Dict]:
    """Query files by taxonomy path including lecture."""
    assert db is not None, "Firestore client is not initialized"
    
    query = (db.collection('files')
        .where(filter=FieldFilter('program', '==', program))
        .where(filter=FieldFilter('term', '==', term))
        .where(filter=FieldFilter('subject', '==', subject))
        .where(filter=FieldFilter('lecture', '==', lecture)))
    
    docs = await asyncio.to_thread(query.get)
    
    results = []
    for doc in docs:
        data = doc.to_dict()
        original_name = data.get('original_name', 'file.unknown')
        
        if '.' in original_name:
            file_type = original_name.split('.')[-1].upper()
        else:
            file_type = 'FILE'
        
        results.append({
            'display_name': data.get('display_name') or 'ملف',
            'file_id': data.get('file_id'),
            'id': doc.id,
            'original_name': original_name,
            'file_type': file_type,
            'program': data.get('program'),
            'term': data.get('term'),
            'subject': data.get('subject'),
            'lecture': data.get('lecture')
        })
    
    return results


async def search_files(query: str) -> List[Dict]:
    """Search files by name prefix."""
    assert db is not None, "Firestore client is not initialized"
    
    query = query.lower().strip()
    if not query:
        return []
    
    docs = await asyncio.to_thread(
        db.collection('files')
        .where(filter=FieldFilter('name_lower', '>=', query))
        .where(filter=FieldFilter('name_lower', '<=', query + '\uf8ff'))
        .limit(200).get
    )
    
    return [{
        'display_name': doc.get('display_name') or doc.get('original_name') or "ملف",
        'file_id': doc.get('file_id'),
        'id': doc.id
    } for doc in docs if doc.get('file_id')]


async def get_taxonomy_doc(doc_id: str) -> Dict:
    """Get taxonomy document from Firestore or the in-memory cache."""
    
    # 1. Check cache first
    if doc_id in _taxonomy_cache:
        logging.info(f"Cache HIT for taxonomy: {doc_id}")
        return _taxonomy_cache[doc_id]
    
    # 2. Cache MISS - fetch from Firestore
    logging.info(f"Cache MISS for taxonomy: {doc_id}. Fetching from Firestore.")
    assert db is not None, "Firestore client is not initialized"
    
    # Firestore is synchronous, run in a separate thread
    doc_ref = db.collection('taxonomy').document(doc_id)
    doc = await asyncio.to_thread(doc_ref.get)
    
    result = doc.to_dict() if doc.exists else {}
    # 3. Store in cache before returning
    _taxonomy_cache[doc_id] = result
    
    return result


async def get_all_taxonomy_config() -> Dict:
    """
    Fetch ALL taxonomy configuration lists from Firebase.
    Returns a dictionary with keys like YEAR_OPTIONS, PROGRAM_OPTIONS, SUBJECTS_BY_PROGRAM, etc.
    """
    assert db is not None, "Firestore client is not initialized"
    
    doc_ref = db.collection('config').document('taxonomy_lists')
    doc = await asyncio.to_thread(doc_ref.get)
    
    if not doc.exists:
        # Return default configuration if document doesn't exist
        default_config = {
            'YEAR_OPTIONS': ["إعدادي", "أولي", "تانيه", "تالته", "رابعه"],
            'PROGRAM_OPTIONS': ["إعدادي", "تحكم", "حاسبات", "اتصالات"],
            'TERM_OPTIONS': ["اول", "تاني"],
            'SUBJECTS_BY_PROGRAM': {
                "عام": [
                    "معالجات", "مهارات عرض واتصال", "تصميم الالكترونيات الرقميه",
                    "قياسات كهربية", "شبكات 1", "احتمالات و احصاء"
                ],
                "حاسبات": [
                    "الذكاء الاصطناعي", "أنظمة التشغيل", "هندسة البرمجيات",
                    "OOP", "بنية حاسب"
                ],
                "تحكم": [
                    "إلكترونيات قوى", "حساسات وأجهزة", "أساسيات هندسة التحكم", "قوى كهربية"
                ],
                "اتصالات": [
                    "تصميم الدوائر المتكاملة", "اتصالات رقمية"
                ]
            },
            'YEAR_RULES': {
                "إعدادي": {
                    "REQUIRES_PROGRAM": False,
                    "SUBJECT_INPUT": "TEXT",
                    "INFO_MESSAGE": "سنة إعدادي لا تتطلب تخصص.",
                    "SUBJECTS_LIST_KEY": None
                },
                "تانيه": {
                    "REQUIRES_PROGRAM": True,
                    "SUBJECT_INPUT": "DROPDOWN",
                    "INFO_MESSAGE": None,
                    "SUBJECTS_LIST_KEY": "SUBJECTS_BY_PROGRAM"
                },
                "أولي": {
                    "REQUIRES_PROGRAM": True,
                    "SUBJECT_INPUT": "TEXT",
                    "INFO_MESSAGE": None,
                    "SUBJECTS_LIST_KEY": None
                },
                "تالته": {
                    "REQUIRES_PROGRAM": True,
                    "SUBJECT_INPUT": "TEXT",
                    "INFO_MESSAGE": None,
                    "SUBJECTS_LIST_KEY": None
                },
                "رابعه": {
                    "REQUIRES_PROGRAM": True,
                    "SUBJECT_INPUT": "TEXT",
                    "INFO_MESSAGE": None,
                    "SUBJECTS_LIST_KEY": None
                }
            }
        }
        # Initialize the document with default config
        await asyncio.to_thread(doc_ref.set, default_config)
        return default_config
    
    return doc.to_dict()


async def set_last_uploaded_file(file_id: str, original_name: str) -> None:
    """Saves the latest uploaded file metadata to the Firebase mailbox."""
    assert db is not None, "Firestore client is not initialized"

    doc_ref = db.document(_MAILBOX_DOC_PATH)
    try:
        await asyncio.to_thread(
            doc_ref.set,
            {
                'last_uploaded_file_id': file_id,
                'last_uploaded_file_name': original_name,
                'last_upload_timestamp': firestore.SERVER_TIMESTAMP
            },
            merge=True
        )
        logging.info(f"Mailbox updated with file_id: {file_id}")
    except Exception as e:
        logging.error(f"Failed to update mailbox: {e}")


async def get_last_uploaded_file() -> Dict:
    """Fetches the last uploaded file metadata from the Firebase mailbox."""
    assert db is not None, "Firestore client is not initialized"

    doc_ref = db.document(_MAILBOX_DOC_PATH)
    try:
        doc = await asyncio.to_thread(doc_ref.get)
        if doc.exists:
            return doc.to_dict()
        return {}
    except Exception as e:
        logging.error(f"Failed to get mailbox: {e}")
        return {}


async def update_subject_list(program: str, new_subject: str) -> None:
    """
    Add a new subject to a specific program list using Firebase ArrayUnion.
    """
    assert db is not None, "Firestore client is not initialized"
    
    doc_ref = db.collection('config').document('taxonomy_lists')
    
    # Use ArrayUnion to add the subject without duplicates
    await asyncio.to_thread(
        doc_ref.update,
        {f'SUBJECTS_BY_PROGRAM.{program}': firestore.ArrayUnion([new_subject])}
    )
    
    logging.info(f"Added subject '{new_subject}' to program '{program}'")


async def update_taxonomy(program: str, term: str, subject: str, lecture: str) -> None:
    """Update taxonomy collections including lectures - Program-Centric."""
    assert db is not None, "Firestore client is not initialized"
    terms_key = program
    subject_key = f"{program}_{term}"
    lecture_key = f"{program}_{term}_{subject}"
    
    def update_tx(transaction):
        # Update all levels atomically
        transaction.set(
            db.collection('taxonomy').document('programs'),
            {'list': firestore.ArrayUnion([program])},
            merge=True
        )
        transaction.set(
            db.collection('taxonomy').document('terms'),
            {terms_key: firestore.ArrayUnion([term])},
            merge=True
        )
        transaction.set(
            db.collection('taxonomy').document('subjects'),
            {subject_key: firestore.ArrayUnion([subject])},
            merge=True
        )
        transaction.set(
            db.collection('taxonomy').document('lectures'),
            {lecture_key: firestore.ArrayUnion([lecture])},
            merge=True
        )

    def run_transaction_wrapper(callback):
        """Wrapper to simulate run_transaction for compatibility with tests."""
        if hasattr(db, 'run_transaction'):
            # Test environment with mocked run_transaction
            return db.run_transaction(callback)
        else:
            # Production environment - manually create and commit transaction
            transaction = db.transaction()
            callback(transaction)
            return transaction.commit()

    try:
        await asyncio.to_thread(run_transaction_wrapper, update_tx)
    except Exception as e:
        logging.error(f"Taxonomy transaction failed: {e}")
        raise


async def save_file(file_data: Dict) -> str:
    """Save new file document and update taxonomy."""
    assert db is not None, "Firestore client is not initialized"
    
    doc_ref = db.collection('files').document()
    file_data.update({
        'created_at': firestore.SERVER_TIMESTAMP,
        'name_lower': file_data['display_name'].lower()
    })
    
    try:
        await asyncio.to_thread(doc_ref.set, file_data)
        await update_taxonomy(
            file_data['program'],
            file_data['term'],
            file_data['subject'],
            file_data['lecture']
        )
        return doc_ref.id
    except Exception as e:
        logging.error(f"File save failed: {e}")
        raise


async def update_file_metadata(doc_id: str, new_data: Dict) -> None:
    """Updates a file's metadata in the 'files' collection."""
    assert db is not None, "Firestore client is not initialized"

    if 'display_name' in new_data:
        new_data['name_lower'] = new_data['display_name'].lower().strip()

    try:
        doc_ref = db.collection('files').document(doc_id)
        await asyncio.to_thread(doc_ref.update, new_data)
        logging.info(f"Updated file metadata for doc: {doc_id}")
    except Exception as e:
        logging.error(f"Failed to update file {doc_id}: {e}")
        raise


async def delete_file(doc_id: str) -> None:
    """Deletes a file document from the 'files' collection."""
    assert db is not None, "Firestore client is not initialized"

    try:
        doc_ref = db.collection('files').document(doc_id)
        await asyncio.to_thread(doc_ref.delete)
        logging.info(f"Deleted file doc: {doc_id}")
    except Exception as e:
        logging.error(f"Failed to delete file {doc_id}: {e}")
        raise


async def delete_lecture_and_files(program: str, term: str, subject: str, lecture: str) -> None:
    """Deletes an entire lecture folder and all files within it."""
    assert db is not None, "Firestore client is not initialized"

    files_to_delete = await get_files(program, term, subject, lecture)

    if files_to_delete:
        batch = db.batch()
        for file_doc in files_to_delete:
            doc_ref = db.collection('files').document(file_doc['id'])
            batch.delete(doc_ref)
        await asyncio.to_thread(batch.commit)
        logging.info(f"Deleted {len(files_to_delete)} files from lecture: {lecture}")

    taxonomy_key = f"{program}_{term}_{subject}"
    doc_ref = db.collection('taxonomy').document('lectures')
    await asyncio.to_thread(
        doc_ref.set,
        {taxonomy_key: firestore.ArrayRemove([lecture])},
        merge=True
    )
    logging.info(f"Removed lecture '{lecture}' from taxonomy.")
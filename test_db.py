"""Unit tests for db.py Data Access Layer"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
import asyncio
from google.cloud.firestore_v1.base_query import FieldFilter

# We must patch firebase_admin BEFORE importing db
mock_firebase = MagicMock()
mock_firestore = MagicMock()
mock_client = MagicMock()

@pytest.fixture(autouse=True)
def setup_firebase_mocks():
    """
    Setup Firebase mocks before any tests run.
    The 'autouse=True' ensures this runs before every test.
    """
    with patch.dict('sys.modules', {
        'firebase_admin': mock_firebase,
        'firebase_admin.credentials': MagicMock(),
        'firebase_admin.firestore': mock_firestore
    }):
        mock_firestore.client.return_value = mock_client
        # Now we can safely import db
        import db
        # Make the mock client available to db module
        db.db = mock_client
        yield db  # This makes 'db' available to tests
        # Cleanup after each test
        db.db = None

@pytest.mark.asyncio
async def test_get_files(setup_firebase_mocks):
    """Test get_files query construction with correct FieldFilters"""
    db = setup_firebase_mocks
    mock_collection = MagicMock()
    mock_query = MagicMock()
    mock_client.collection.return_value = mock_collection
    mock_collection.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.get.return_value = []

    # Test data
    year, program, term, subject, lecture = "تانيه", "حاسبات", "اول", "OOP", "محاضرة 1"
    
    # Call the function
    await db.get_files(year, program, term, subject, lecture)
    
    # Check the first call
    first_call_args = mock_collection.where.call_args[1]
    assert isinstance(first_call_args['filter'], FieldFilter)
    assert first_call_args['filter'].field_path == 'year'  # Fixed: removed underscore
    # Check the 4 subsequent calls
    assert mock_query.where.call_count == 4

@pytest.mark.asyncio
async def test_search_files(setup_firebase_mocks):
    """Test search_files prefix search logic"""
    db = setup_firebase_mocks
    mock_collection = MagicMock()
    mock_query = MagicMock()
    mock_client.collection.return_value = mock_collection
    mock_collection.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.get.return_value = []

    # Test search
    await db.search_files("test")
    
    # Check first call on the COLLECTION
    mock_collection.where.assert_called_once()
    call_args_1 = mock_collection.where.call_args[1]
    assert call_args_1['filter'].field_path == 'name_lower'
    assert call_args_1['filter'].op_string == '>='

    # Check second call on the QUERY
    mock_query.where.assert_called_once()
    call_args_2 = mock_query.where.call_args[1]
    assert call_args_2['filter'].field_path == 'name_lower'
    assert call_args_2['filter'].op_string == '<='
    assert call_args_2['filter'].value == 'test\uf8ff'
    
    mock_query.limit.assert_called_with(200)  # Fixed: add assert_

@pytest.mark.asyncio
async def test_save_file(setup_firebase_mocks):
    """
    Test save_file metadata construction
    """
    db = setup_firebase_mocks
    mock_doc_ref = MagicMock()
    mock_client.collection().document.return_value = mock_doc_ref
    
    # Test data
    file_data = {
        'display_name': 'Test File',
        'original_name': 'test.pdf',
        'year': 'تانيه',
        'program': 'حاسبات',
        'term': 'اول',
        'subject': 'OOP',
        'lecture': 'محاضرة 1'
    }
    
    # Mock the update_taxonomy call since we test it separately
    with patch.object(db, 'update_taxonomy', new_callable=AsyncMock) as mock_update:
        await db.save_file(file_data)
        
        # Verify the document data
        set_call = mock_doc_ref.set.call_args[0][0]
        assert set_call['name_lower'] == 'test file'
        assert 'created_at' in set_call
        assert mock_update.called

@pytest.mark.asyncio
async def test_update_taxonomy(setup_firebase_mocks):
    """Test taxonomy update transaction logic"""
    db = setup_firebase_mocks
    mock_transaction = MagicMock()

    # Fix: Mock the run_transaction method instead of transaction()
    mock_client.run_transaction = MagicMock(side_effect=lambda callback: callback(mock_transaction))

    # Test data
    year = "تانيه"
    program = "حاسبات"
    term = "اول"
    subject = "OOP"
    lecture = "محاضرة 1"

    await db.update_taxonomy(year, program, term, subject, lecture)

    # Verify transaction calls
    assert mock_transaction.set.call_count == 5

    # Verify the ArrayUnion calls
    calls = mock_transaction.set.call_args_list
    for call_obj in calls:
        _, kwargs = call_obj
        assert kwargs['merge'] is True
        data = call_obj[0][1]  # The data dict passed to set()
        assert list(data.values())[0].values  # Verify it's an ArrayUnion

@pytest.mark.asyncio
async def test_concurrent_taxonomy_updates(setup_firebase_mocks):
    """Ensure TTLCache and transactions behave correctly under concurrent access."""
    db = setup_firebase_mocks
    mock_client = db.db

    taxonomy_collection = MagicMock()
    files_collection = MagicMock()
    config_collection = MagicMock()

    def collection_side_effect(name):
        if name == 'taxonomy':
            return taxonomy_collection
        if name == 'files':
            return files_collection
        if name == 'config':
            return config_collection
        return MagicMock()

    mock_client.collection.side_effect = collection_side_effect

    taxonomy_doc_ref = MagicMock()
    taxonomy_doc_snapshot = MagicMock()
    taxonomy_doc_snapshot.exists = True
    taxonomy_doc_snapshot.to_dict.return_value = {'list': ['إعدادي', 'تانيه']}

    def document_side_effect(doc_id):
        if doc_id == 'years':
            return taxonomy_doc_ref
        return MagicMock()

    taxonomy_collection.document.side_effect = document_side_effect
    taxonomy_doc_ref.get.return_value = taxonomy_doc_snapshot

    db._taxonomy_cache.clear()

    results = await asyncio.gather(*[db.get_taxonomy_doc('years') for _ in range(10)])

    assert all(result == {'list': ['إعدادي', 'تانيه']} for result in results)
    assert 1 <= taxonomy_doc_ref.get.call_count <= 10
    assert 'years' in db._taxonomy_cache

    mock_transaction = MagicMock()
    mock_client.run_transaction = MagicMock(side_effect=lambda callback: callback(mock_transaction))

    async def perform_upload(idx: int):
        await db.update_taxonomy(
            year="تانيه",
            program=f"حاسبات-{idx}",
            term=f"اول-{idx}",
            subject=f"مادة-{idx}",
            lecture=f"محاضرة-{idx}"
        )

    await asyncio.gather(*(perform_upload(i) for i in range(10)))

    assert mock_client.run_transaction.call_count == 10
    assert mock_transaction.set.call_count == 50
    for call_obj in mock_transaction.set.call_args_list:
        _, kwargs = call_obj
        assert kwargs.get('merge') is True

    mock_client.collection.side_effect = None

@pytest.mark.asyncio
async def test_search_files_empty_query(setup_firebase_mocks):
    """Test search_files with empty query string returns empty list without DB call"""
    db = setup_firebase_mocks
    mock_client.reset_mock()  # Clear any previous calls
    
    results = await db.search_files("")
    
    assert results == []
    mock_client.collection.assert_not_called()

@pytest.mark.asyncio
async def test_get_taxonomy_doc_not_found(setup_firebase_mocks):
    """Test get_taxonomy_doc returns default empty list when doc not found"""
    db = setup_firebase_mocks
    
    # Mock document not found
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_doc.to_dict.return_value = {}
    mock_collection = MagicMock()
    mock_doc_ref = MagicMock()
    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_doc_ref
    mock_doc_ref.get.return_value = mock_doc
    
    result = await db.get_taxonomy_doc("invalid_doc")
    
    assert result == {}
    mock_collection.document.assert_called_once_with("invalid_doc")

@pytest.mark.asyncio
async def test_get_file_details_not_found(setup_firebase_mocks):
    """Test get_file_details returns empty dict when file not found"""
    db = setup_firebase_mocks
    
    # Mock document not found
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_doc.to_dict.return_value = {}
    mock_collection = MagicMock()
    mock_doc_ref = MagicMock()
    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_doc_ref
    mock_doc_ref.get.return_value = mock_doc
    
    result = await db.get_file_details("invalid_doc_id")
    
    assert result == {}
    mock_collection.document.assert_called_once_with("invalid_doc_id")

if __name__ == '__main__':
    pytest.main(['-v', 'test_db.py'])

"""
Performance Testing for SGDI
Tests load handling, file upload performance, search performance, and page load times
"""
import pytest
import time
import io
import concurrent.futures
from app.models.document import Documento, Categoria
from app.models.user import User


class TestConcurrentUsers:
    """Test system performance with multiple concurrent users"""
    
    def test_concurrent_login_requests(self, app, test_user):
        """Test handling multiple concurrent login requests"""
        client = app.test_client()
        
        def login_request():
            response = client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'TestPassword123!'
            })
            return response.status_code
        
        # Simulate 50 concurrent login attempts
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(login_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should complete
        assert len(results) == 50
        
        # Most should succeed (200 or 302)
        successful = sum(1 for r in results if r in [200, 302])
        assert successful > 40  # At least 80% success rate
        
        # Should complete in reasonable time (less than 10 seconds)
        assert duration < 10.0
        
        print(f"\n50 concurrent logins completed in {duration:.2f} seconds")
    
    def test_concurrent_document_views(self, app, test_user, test_category, db_session):
        """Test handling multiple concurrent document view requests"""
        # Create test documents
        documents = []
        for i in range(10):
            doc = Documento(
                nome=f'Test Document {i}',
                descricao=f'Document {i} for testing',
                caminho_arquivo=f'/uploads/test{i}.pdf',
                nome_arquivo_original=f'test{i}.pdf',
                tamanho_bytes=1024,
                tipo_mime='application/pdf',
                hash_arquivo=f'hash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
            documents.append(doc)
        
        db_session.session.commit()
        
        client = app.test_client()
        
        # Login first
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        def view_document(doc_id):
            response = client.get(f'/documents/{doc_id}')
            return response.status_code
        
        # Simulate 100 concurrent document views
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            doc_ids = [doc.id for doc in documents] * 10  # View each doc 10 times
            futures = [executor.submit(view_document, doc_id) for doc_id in doc_ids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should complete
        assert len(results) == 100
        
        # Should complete in reasonable time
        assert duration < 15.0
        
        print(f"\n100 concurrent document views completed in {duration:.2f} seconds")
    
    def test_concurrent_search_requests(self, app, test_user, test_category, db_session):
        """Test handling multiple concurrent search requests"""
        # Create test documents
        for i in range(20):
            doc = Documento(
                nome=f'Searchable Document {i}',
                descricao=f'Content for search testing {i}',
                caminho_arquivo=f'/uploads/search{i}.pdf',
                nome_arquivo_original=f'search{i}.pdf',
                tamanho_bytes=1024,
                tipo_mime='application/pdf',
                hash_arquivo=f'searchhash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
        
        db_session.session.commit()
        
        client = app.test_client()
        
        # Login first
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        def search_request(query):
            response = client.get(f'/search?q={query}')
            return response.status_code
        
        # Simulate 100 concurrent searches
        start_time = time.time()
        
        queries = ['Searchable', 'Document', 'Content', 'testing'] * 25
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(search_request, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should complete
        assert len(results) == 100
        
        # Should complete in reasonable time
        assert duration < 20.0
        
        print(f"\n100 concurrent searches completed in {duration:.2f} seconds")


class TestFileUploadPerformance:
    """Test file upload performance"""
    
    def test_single_file_upload_time(self, authenticated_client, test_category):
        """Test time to upload a single file"""
        # Create a 5MB test file
        file_size = 5 * 1024 * 1024  # 5MB
        file_content = b'x' * file_size
        
        data = {
            'file': (io.BytesIO(file_content), 'large_test.pdf'),
            'nome': 'Large Test Document',
            'descricao': 'Performance test document',
            'categoria_id': test_category.id
        }
        
        start_time = time.time()
        
        response = authenticated_client.post(
            '/documents/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete successfully
        assert response.status_code in [200, 302]
        
        # Should upload in reasonable time (less than 5 seconds for 5MB)
        assert duration < 5.0
        
        print(f"\n5MB file upload completed in {duration:.2f} seconds")
    
    def test_multiple_file_uploads(self, authenticated_client, test_category):
        """Test uploading multiple files"""
        files_to_upload = 5
        upload_times = []
        
        for i in range(files_to_upload):
            # Create a 1MB test file
            file_size = 1 * 1024 * 1024  # 1MB
            file_content = b'x' * file_size
            
            data = {
                'file': (io.BytesIO(file_content), f'test_{i}.pdf'),
                'nome': f'Test Document {i}',
                'descricao': f'Test {i}',
                'categoria_id': test_category.id
            }
            
            start_time = time.time()
            
            response = authenticated_client.post(
                '/documents/upload',
                data=data,
                content_type='multipart/form-data'
            )
            
            end_time = time.time()
            duration = end_time - start_time
            upload_times.append(duration)
            
            assert response.status_code in [200, 302]
        
        # Calculate average upload time
        avg_time = sum(upload_times) / len(upload_times)
        
        # Average should be reasonable (less than 3 seconds per 1MB file)
        assert avg_time < 3.0
        
        print(f"\nAverage upload time for 1MB files: {avg_time:.2f} seconds")
    
    def test_concurrent_file_uploads(self, app, test_user, test_category, db_session):
        """Test handling multiple concurrent file uploads"""
        client = app.test_client()
        
        # Login first
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = True
        
        def upload_file(index):
            file_size = 1 * 1024 * 1024  # 1MB
            file_content = b'x' * file_size
            
            data = {
                'file': (io.BytesIO(file_content), f'concurrent_{index}.pdf'),
                'nome': f'Concurrent Upload {index}',
                'descricao': f'Test {index}',
                'categoria_id': test_category.id
            }
            
            response = client.post(
                '/documents/upload',
                data=data,
                content_type='multipart/form-data'
            )
            return response.status_code
        
        # Simulate 10 concurrent uploads
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_file, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All uploads should complete
        assert len(results) == 10
        
        # Should complete in reasonable time
        assert duration < 30.0
        
        print(f"\n10 concurrent 1MB uploads completed in {duration:.2f} seconds")


class TestSearchPerformance:
    """Test search performance"""
    
    def test_search_with_large_dataset(self, authenticated_client, test_user, test_category, db_session):
        """Test search performance with many documents"""
        # Create 100 test documents
        for i in range(100):
            doc = Documento(
                nome=f'Performance Test Document {i}',
                descricao=f'This is document number {i} for performance testing',
                caminho_arquivo=f'/uploads/perf{i}.pdf',
                nome_arquivo_original=f'perf{i}.pdf',
                tamanho_bytes=1024,
                tipo_mime='application/pdf',
                hash_arquivo=f'perfhash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
        
        db_session.session.commit()
        
        # Perform search
        start_time = time.time()
        
        response = authenticated_client.get('/search?q=Performance')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete successfully
        assert response.status_code == 200
        
        # Should complete in less than 3 seconds
        assert duration < 3.0
        
        print(f"\nSearch across 100 documents completed in {duration:.2f} seconds")
    
    def test_advanced_search_performance(self, authenticated_client, test_user, test_category, db_session):
        """Test advanced search with filters"""
        # Create test documents
        for i in range(50):
            doc = Documento(
                nome=f'Advanced Search Doc {i}',
                descricao=f'Document {i}',
                caminho_arquivo=f'/uploads/adv{i}.pdf',
                nome_arquivo_original=f'adv{i}.pdf',
                tamanho_bytes=1024 * (i + 1),
                tipo_mime='application/pdf',
                hash_arquivo=f'advhash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
        
        db_session.session.commit()
        
        # Perform advanced search with filters
        start_time = time.time()
        
        response = authenticated_client.get(
            f'/search?q=Advanced&categoria_id={test_category.id}&tipo_mime=application/pdf'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete successfully
        assert response.status_code == 200
        
        # Should complete in less than 3 seconds
        assert duration < 3.0
        
        print(f"\nAdvanced search with filters completed in {duration:.2f} seconds")
    
    def test_search_pagination_performance(self, authenticated_client, test_user, test_category, db_session):
        """Test search pagination performance"""
        # Create many documents
        for i in range(200):
            doc = Documento(
                nome=f'Pagination Test {i}',
                descricao=f'Document {i}',
                caminho_arquivo=f'/uploads/page{i}.pdf',
                nome_arquivo_original=f'page{i}.pdf',
                tamanho_bytes=1024,
                tipo_mime='application/pdf',
                hash_arquivo=f'pagehash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
        
        db_session.session.commit()
        
        # Test first page
        start_time = time.time()
        response = authenticated_client.get('/search?q=Pagination&page=1')
        end_time = time.time()
        duration_page1 = end_time - start_time
        
        assert response.status_code == 200
        assert duration_page1 < 3.0
        
        # Test middle page
        start_time = time.time()
        response = authenticated_client.get('/search?q=Pagination&page=5')
        end_time = time.time()
        duration_page5 = end_time - start_time
        
        assert response.status_code == 200
        assert duration_page5 < 3.0
        
        print(f"\nPagination - Page 1: {duration_page1:.2f}s, Page 5: {duration_page5:.2f}s")


class TestPageLoadTimes:
    """Test page load times"""
    
    def test_login_page_load_time(self, client):
        """Test login page load time"""
        start_time = time.time()
        response = client.get('/auth/login')
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 2.0
        
        print(f"\nLogin page loaded in {duration:.2f} seconds")
    
    def test_document_list_page_load_time(self, authenticated_client, test_user, test_category, db_session):
        """Test document list page load time"""
        # Create some documents
        for i in range(20):
            doc = Documento(
                nome=f'List Test Doc {i}',
                descricao=f'Document {i}',
                caminho_arquivo=f'/uploads/list{i}.pdf',
                nome_arquivo_original=f'list{i}.pdf',
                tamanho_bytes=1024,
                tipo_mime='application/pdf',
                hash_arquivo=f'listhash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
        
        db_session.session.commit()
        
        start_time = time.time()
        response = authenticated_client.get('/documents')
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 2.0
        
        print(f"\nDocument list page loaded in {duration:.2f} seconds")
    
    def test_document_detail_page_load_time(self, authenticated_client, test_user, test_category, db_session):
        """Test document detail page load time"""
        # Create a document
        doc = Documento(
            nome='Detail Test Document',
            descricao='Document for detail page testing',
            caminho_arquivo='/uploads/detail.pdf',
            nome_arquivo_original='detail.pdf',
            tamanho_bytes=1024,
            tipo_mime='application/pdf',
            hash_arquivo='detailhash',
            categoria_id=test_category.id,
            usuario_id=test_user.id,
            versao_atual=1,
            status='ativo'
        )
        db_session.session.add(doc)
        db_session.session.commit()
        
        start_time = time.time()
        response = authenticated_client.get(f'/documents/{doc.id}')
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 2.0
        
        print(f"\nDocument detail page loaded in {duration:.2f} seconds")
    
    def test_admin_dashboard_load_time(self, admin_client):
        """Test admin dashboard load time"""
        start_time = time.time()
        response = admin_client.get('/admin/dashboard')
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code in [200, 302]
        assert duration < 3.0
        
        print(f"\nAdmin dashboard loaded in {duration:.2f} seconds")


class TestDatabasePerformance:
    """Test database query performance"""
    
    def test_document_query_performance(self, db_session, test_user, test_category):
        """Test document query performance"""
        # Create many documents
        for i in range(500):
            doc = Documento(
                nome=f'Query Test {i}',
                descricao=f'Document {i}',
                caminho_arquivo=f'/uploads/query{i}.pdf',
                nome_arquivo_original=f'query{i}.pdf',
                tamanho_bytes=1024,
                tipo_mime='application/pdf',
                hash_arquivo=f'queryhash{i}',
                categoria_id=test_category.id,
                usuario_id=test_user.id,
                versao_atual=1,
                status='ativo'
            )
            db_session.session.add(doc)
        
        db_session.session.commit()
        
        # Test query performance
        start_time = time.time()
        documents = db_session.session.query(Documento).filter_by(
            usuario_id=test_user.id,
            status='ativo'
        ).limit(50).all()
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(documents) == 50
        assert duration < 1.0
        
        print(f"\nQueried 50 documents from 500 in {duration:.2f} seconds")
    
    def test_category_hierarchy_query_performance(self, db_session):
        """Test category hierarchy query performance"""
        # Create category hierarchy
        root_categories = []
        for i in range(10):
            root = Categoria(
                nome=f'Root Category {i}',
                descricao=f'Root {i}',
                ativo=True
            )
            db_session.session.add(root)
            root_categories.append(root)
        
        db_session.session.commit()
        
        # Add subcategories
        for root in root_categories:
            for j in range(5):
                sub = Categoria(
                    nome=f'Sub {root.nome} - {j}',
                    descricao=f'Subcategory {j}',
                    categoria_pai_id=root.id,
                    ativo=True
                )
                db_session.session.add(sub)
        
        db_session.session.commit()
        
        # Test query performance
        start_time = time.time()
        categories = db_session.session.query(Categoria).filter_by(ativo=True).all()
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(categories) == 60  # 10 root + 50 sub
        assert duration < 1.0
        
        print(f"\nQueried 60 categories in {duration:.2f} seconds")

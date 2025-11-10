"""
Pytest configuration and fixtures
"""
import pytest
import os
import tempfile
from app import create_app, db
from app.models.user import User, Perfil
from app.models.document import Documento, Categoria
from types import SimpleNamespace
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    # Create a temporary directory for uploads
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def test_user(db_session):
    """Create a test user"""
    # Create perfil first
    perfil = Perfil(
        nome='Usuario',
        descricao='Usuario padrao',
        pode_criar_documentos=True,
        pode_editar_proprios=True,
        pode_excluir_proprios=True,
        pode_visualizar_todos=False,
        pode_editar_todos=False,
        pode_excluir_todos=False,
        pode_gerenciar_usuarios=False,
        pode_gerenciar_categorias=False,
        pode_gerenciar_workflows=False,
        pode_visualizar_auditoria=False
    )
    db_session.session.add(perfil)
    db_session.session.commit()
    
    user = User(
        nome='Test User',
        email='test@example.com',
        perfil_id=perfil.id,
        ativo=True
    )
    user.set_password('TestPassword123!')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def admin_user(db_session):
    """Create an admin user"""
    # Create admin perfil
    perfil = Perfil(
        nome='Administrador',
        descricao='Administrador do sistema',
        pode_criar_documentos=True,
        pode_editar_proprios=True,
        pode_excluir_proprios=True,
        pode_visualizar_todos=True,
        pode_editar_todos=True,
        pode_excluir_todos=True,
        pode_gerenciar_usuarios=True,
        pode_gerenciar_categorias=True,
        pode_gerenciar_workflows=True,
        pode_visualizar_auditoria=True
    )
    db_session.session.add(perfil)
    db_session.session.commit()
    
    user = User(
        nome='Admin User',
        email='admin@example.com',
        perfil_id=perfil.id,
        ativo=True
    )
    user.set_password('AdminPassword123!')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def test_category(db_session):
    """Create a test category"""
    categoria = Categoria(
        nome='Test Category',
        descricao='Test category description',
        ativo=True
    )
    db_session.session.add(categoria)
    db_session.session.commit()
    # Return a lightweight object with only the attributes tests need (primarily .id)
    # This avoids DetachedInstanceError in concurrent tests where ORM instances
    # might be detached from their session when accessed in worker threads.
    return SimpleNamespace(id=categoria.id)


@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Create authenticated test client"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture(scope='function')
def admin_client(client, admin_user):
    """Create authenticated admin client"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client

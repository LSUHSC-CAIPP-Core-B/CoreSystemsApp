import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Role
from werkzeug.security import generate_password_hash
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        
        # Create test roles
        admin_role = Role(role="admin")
        user_role = Role(role="user")
        coreb_role = Role(role="coreB")
        corec_role = Role(role="coreC")
        
        db.session.add_all([admin_role, user_role, coreb_role, corec_role])
        db.session.commit()
        
        # Create test users
        test_user = User(
            email="test@example.com",
            name="Test User",
            password=generate_password_hash("password")
        )
        test_user.urole.append(user_role)
        
        test_admin = User(
            email="admin@example.com",
            name="Admin User",
            password=generate_password_hash("admin")
        )
        test_admin.urole.extend([admin_role, user_role, coreb_role, corec_role])
        
        db.session.add_all([test_user, test_admin])
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """Create an authenticated test client."""
    client.post('/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    return client

@pytest.fixture
def mock_db_config(tmp_path):
    """Create temporary database config files."""
    config_dir = tmp_path / "db_config"
    config_dir.mkdir()
    
    coreb_config = config_dir / "CoreB.json"
    coreb_config.write_text('{"db_config": {"host": "localhost", "database": "test_coreb", "user": "test", "password": "test"}}')
    
    corec_config = config_dir / "CoreC.json"
    corec_config.write_text('{"db_config": {"host": "localhost", "database": "test_corec", "user": "test", "password": "test"}}')
    
    return str(config_dir)

import pytest
from app.models import User, Role

def test_user_properties(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@example.com").first()
        
        assert user.is_admin is True
        assert user.is_core_b is True
        assert user.is_core_c is True
        assert user.is_super_admin is True

def test_regular_user_properties(app):
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        
        assert user.is_admin is False
        assert user.is_super_admin is False

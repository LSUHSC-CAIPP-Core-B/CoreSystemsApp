from flask_login import UserMixin
from . import db

# Database models used for user credentials
# User has a custom properties of roles to determine access level

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    urole = db.relationship('Role', secondary='userhasrole', back_populates='user')

    def get_role(self):
        return self.urole
    
    @property
    def is_admin(self):
        for ur in self.urole:
            if ur.role == "admin":
                return True
        return False
    
    @property
    def is_core_b(self):
        for ur in self.urole:
            if ur.role == "coreB":
                return True
        return False
    
    @property
    def is_core_c(self):
        for ur in self.urole:
            if ur.role == "coreC":
                return True
        return False
    
    @property    
    def is_super_admin(self):
        if self.is_admin and self.is_core_b and self.is_core_c:
            return True
        else:
            return False

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50))
    user = db.relationship('User', secondary='userhasrole', back_populates='urole')

class UserHasRole(db.Model):
    __tablename__ = "userhasrole"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

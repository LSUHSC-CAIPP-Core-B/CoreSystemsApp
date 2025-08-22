from functools import wraps
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy_utils import database_exists

from config import Config

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

# Initialize login manager
login_manager = LoginManager()

# Overwrite of flask-login @login_required decorator
# Check if user logged in and if has needed role
def login_required(role=[]):
    """
    Function to check if user is logged in and if yes checks needed permisions
    guide: https://stackoverflow.com/questions/15871391/implementing-flask-login-with-multiple-user-classes

    role (list(str)): list of roles required to access the endpoint decorated by this function
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            urole = current_user.urole

            for r in role:
                if r == "any":
                    break
                elif any(ur.role == r for ur in urole):
                    pass
                else:
                    return login_manager.unauthorized()
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# App creation function
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database
    db.init_app(app)
    from .models import User, Role, UserHasRole, Invoice

    # Setup login manager
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    if database_exists(Config.SQLALCHEMY_DATABASE_URI):
        with app.app_context():
            db.create_all()
    else:
        with app.app_context():
            db.create_all()
            admin_role = Role(role="admin")
            user_role = Role(role="user")
            coreb_role = Role(role="coreB")
            _role = Role(role="coreC")
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.add(coreb_role)
            db.session.add(_role)
            db.session.commit()

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        user = User.query.get(int(user_id))
        return user
    

    # Register blueprints here
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    # ! CSV route for core B
    #from app.CoreB.orders.csv_routes import bp as main_bp
    #app.register_blueprint(main_bp)

    from app.CoreB.orders import bp as main_bp
    app.register_blueprint(main_bp)

    from app.CoreB.invoices_list import bp as invoices_bp
    app.register_blueprint(invoices_bp)

    from app.CoreB.pi_list import bp as pi_bp
    app.register_blueprint(pi_bp)

    from app.CoreB.graphs.orders_dashboard import bp as graphs_bp
    app.register_blueprint(graphs_bp)

    from app.CoreC.stock import bp as stock_bp
    app.register_blueprint(stock_bp)

    from app.CoreC.antibodies import bp as antibodies_bp
    app.register_blueprint(antibodies_bp)

    from app.CoreC.panels import bp as panels_bp
    app.register_blueprint(panels_bp)

    from app.CoreC.mouse import bp as mouse_bp
    app.register_blueprint(mouse_bp)

    return app
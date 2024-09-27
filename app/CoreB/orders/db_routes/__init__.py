from flask import Blueprint

bp = Blueprint('orders', __name__)

from app.CoreB.orders.db_routes import routes
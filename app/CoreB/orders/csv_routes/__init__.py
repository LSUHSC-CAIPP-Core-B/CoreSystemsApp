from flask import Blueprint

bp = Blueprint('orders', __name__)

from app.CoreB.orders.csv_routes import routes
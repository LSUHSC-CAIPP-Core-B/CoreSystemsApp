from flask import Blueprint

bp = Blueprint('orders_dashboard', __name__)

from app.CoreB.graphs.orders_dashboard import routes
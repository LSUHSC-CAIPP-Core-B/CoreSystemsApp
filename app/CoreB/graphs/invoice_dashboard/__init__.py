from flask import Blueprint

bp = Blueprint('invoice_dashboard', __name__)

from app.CoreB.graphs.invoice_dashboard import routes
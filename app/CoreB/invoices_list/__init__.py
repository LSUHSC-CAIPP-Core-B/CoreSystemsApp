from flask import Blueprint

bp = Blueprint('invoices_list', __name__)

from app.CoreB.invoices_list import routes
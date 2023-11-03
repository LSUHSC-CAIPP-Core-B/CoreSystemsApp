from flask import Blueprint

bp = Blueprint('stock', __name__)

from app.CoreC.stock import routes
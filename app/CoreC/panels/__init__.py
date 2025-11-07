from flask import Blueprint

bp = Blueprint('panels', __name__)

from app.CoreC.panels import routes

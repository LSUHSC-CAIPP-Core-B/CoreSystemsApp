from flask import Blueprint

bp = Blueprint('mouse', __name__)

from app.CoreC.mouse import routes
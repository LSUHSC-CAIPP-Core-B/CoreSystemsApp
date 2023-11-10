from flask import Blueprint

bp = Blueprint('pi_list', __name__)

from app.CoreB.pi_list import routes
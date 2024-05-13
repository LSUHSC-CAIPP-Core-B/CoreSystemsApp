from flask import Blueprint

bp = Blueprint('antibodies', __name__)

from app.CoreC.antibodies import routes
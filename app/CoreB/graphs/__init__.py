from flask import Blueprint

bp = Blueprint('graphs', __name__)

from app.CoreB.graphs import routes
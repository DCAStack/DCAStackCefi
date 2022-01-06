from flask import Blueprint

bp = Blueprint('dca', __name__)

from project.dca import routes
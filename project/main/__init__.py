from flask import Blueprint

bp = Blueprint('main', __name__)

from project.main import routes
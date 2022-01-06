from flask import Blueprint

bp = Blueprint('dashboard', __name__)

from project.dashboard import routes
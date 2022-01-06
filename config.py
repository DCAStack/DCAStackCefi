import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_BACKEND_URL = os.environ.get('REDIS_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
        'sqlite:///db.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_TLS = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['orderbot@dcastack.com']
    REDIS_URL = os.environ.get('REDIS_URL')
    SET_SANDBOX = True if os.environ.get('SET_SANDBOX') == "true" else False
    IS_DEBUG = True if os.environ.get('SET_DEBUG') == "true" else False
    SENTRY_KEY = os.environ.get('SENTRY_KEY')
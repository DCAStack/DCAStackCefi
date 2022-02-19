from logging import DEBUG
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from celery import Celery
from flask_migrate import Migrate
from celery.schedules import crontab
import logging
from config import Config
import secure
from flask_moment import Moment
from flask_executor import Executor
from sentry_sdk.integrations.flask import FlaskIntegration
import sentry_sdk
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
executor = Executor()
secure_headers = secure.Secure()
SANDBOX_MODE = Config.SET_SANDBOX
DEBUG_MODE = Config.IS_DEBUG
SECRET_KEY = Config.SECRET_KEY
SENTRY_FLASK_KEY = Config.SENTRY_FLASK_KEY
SENTRY_CELERY_KEY = Config.SENTRY_CELERY_KEY
db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)
login_manager = LoginManager()
migrate = Migrate(compare_type=True)
moment = Moment()
DEBUG = True
BEAT_INTERVAL = 5 #5 minutes

if not DEBUG_MODE:
    sentry_sdk.init(
    dsn=SENTRY_FLASK_KEY,
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.8
)

# if SANDBOX_MODE:
#     logging.basicConfig(filename='flaskLogs.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object(config_class)
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['EXECUTOR_MAX_WORKERS'] = 2

    @app.after_request
    def set_secure_headers(response):
        secure_headers.framework.flask(response)
        return response

    app.config.update(
        CELERY_BROKER_URL=app.config['CELERY_BROKER_URL'],
        CELERY_BACKEND_URL=app.config['CELERY_BACKEND_URL'],
        accept_content=['json', 'pickle'],
        beat_schedule={
            'periodic_task': {
                'task': 'project.services.dcaService.run_dcaSchedule',
                'schedule': crontab(minute='*/{}'.format(BEAT_INTERVAL))
            }
        }
    )

    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    celery.conf.update(app.config)

    db.init_app(app)

    with app.app_context():
        if db.engine.url.drivername == 'sqlite':
            migrate.init_app(app, db, render_as_batch=True)
        else:
            migrate.init_app(app, db)

    mail.init_app(app)
    jwt.init_app(app)
    moment.init_app(app)
    executor.init_app(app)
    csrf.init_app(app)

    login_manager.session_protection = "strong"
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from project.authy import bp as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for general main parts of app
    from project.main import bp as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for dca parts of app
    from project.dca import bp as dca_blueprint
    app.register_blueprint(dca_blueprint)

    # blueprint for dashboard parts of app
    from project.dashboard import bp as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)


    app.logger.info("App Created, returning")
    return app


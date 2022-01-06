from flask.cli import FlaskGroup
import logging
from project import create_app


app = create_app()
cli = FlaskGroup(create_app=create_app)


if __name__ == "__main__":
    cli()

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
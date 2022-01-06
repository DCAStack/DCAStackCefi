web: flask db upgrade; gunicorn manage:app --log-level=debug
worker: celery worker -A celery_worker.celery --beat --loglevel=info --concurrency=4

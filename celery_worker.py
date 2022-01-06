#!/usr/bin/env python
import os
from project import celery, create_app, DEBUG_MODE, SENTRY_KEY
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

if not DEBUG_MODE:
    sentry_sdk.init(
        dsn=SENTRY_KEY,
        integrations=[CeleryIntegration()]
    )

app = create_app()
app.app_context().push()
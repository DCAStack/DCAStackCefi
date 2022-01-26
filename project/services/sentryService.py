from sentry_sdk import capture_exception, set_user
from project.models import User


def capture_err(exception,session=None):

    if session:
        if '_user_id' in session:
            retrUser = User.get_user(session['_user_id'])
            set_user({"email": retrUser.email})
            
    capture_exception(exception)


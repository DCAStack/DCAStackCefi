# Welcome to DCA Stack for Centralized Exchanges!
## An Automated Dollar Cost Averaging Bot For Your Crypto

This github repo was made in the spirit of **Don't Trust, Verify**. I totally understand the hesitation of using web apps created by strangers on the internet. Especially when it comes to sensitive information like API keys and your crypto. So to help foster trust and gather early user feedback, I'm releasing the source code that directly builds the production environment. 

## How do I host this?

First, download Docker here: https://www.docker.com/products/docker-desktop

Second, let's see if we can get this webapp going. Open up a terminal, clone this repo and enter the folder. We are going to make a .env file in the current location you are in. Here is what that looks like:

    SECRET_KEY=YouShouldRandomlyGenerateThis
    MAIL_SERVER=YourMailServer
    MAIL_PORT=YourPort
    MAIL_USE_TLS=TrueorFalse
    MAIL_USE_SSL=TrueorFalse
    MAIL_USERNAME=YourMailUsername
    MAIL_PASSWORD=YourMailPassword
    REDIS_URL=redis://redis-server:6379/0
    SET_SANDBOX=False
    SET_DEBUG=False
    SENTRY_FLASK_KEY=Sign up here: https://sentry.io/ and get a client key (DSN) for flask project
    SENTRY_CELERY_KEY=Sign up here: https://sentry.io/ and get a client key (DSN) for celery project

Third, we need a .flaskenv file, add this:

    FLASK_APP=project
    FLASK_ENV=development
    FLASK_DEBUG=1

Fourth, let's do the following outside the REPO directory. This will generate the sqlite DB for working locally.

    python3 -m venv YOUR_ENV_NAME_HERE
    source YOUR_ENV_NAME_HERE/bin/activate
    cd REPO_NAME
    pip install -r requirements.txt
    python3 manage.py db init

Finally, let's get docker up!

    docker-compose up -d --build
    
And that's it. Open your browser to http://localhost:5000 to view the app or to http://localhost:5556 to view the Flower dashboard (this is for viewing celery tasks running).


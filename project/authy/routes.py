from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from project.models import User
from project import db
from project.services.mailService import send_reset_password
from project.authy import bp
from project.authy.forms import LoginForm, SignupForm
from flask import current_app

@bp.route('/reset', methods=['GET', 'POST'])
def reset_password():

    if request.method == 'GET':
        return render_template('authy/reset.html')

    if request.method == 'POST':

        email = request.form.get('email')
        user = User.verify_email(email)

        if user:
            send_reset_password(user)
            return render_template('authy/check.html')

        else:
            flash('Did you type that email in correctly?')
            return redirect(url_for('auth.reset_password'))

@bp.route('/password_reset_verified/<token>', methods=['GET', 'POST'])
def reset_verified(token):

    user = User.verify_reset_token(token)
    if not user:
        print('no user found')
        return redirect(url_for('auth.login'))

    password = request.form.get('password')
    if password:
        user.set_password(password, commit=True)

        return redirect(url_for('auth.login'))

    return render_template('authy/reset_verified.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():

    loginForm = LoginForm()

    if request.method == 'GET':
        return render_template('authy/login.html', form=loginForm)

    if request.method == 'POST':

        email = loginForm.emailField.data
        password = loginForm.passwordField.data

        user = User.query.filter_by(email=email).first()

        # check if user actually exists
        # take the user supplied password, hash it, and compare it to the hashed password in database
        if not user or not check_password_hash(user.password, password): 
            flash('Please check your login details or did you')
            return redirect(url_for('auth.login',form=loginForm)) # if user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(user)
        return redirect(url_for('dca.dcaSetup'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():

    signupForm = SignupForm()

    if request.method == 'GET':
        return render_template('authy/signup.html',form=signupForm), 200

    if request.method == 'POST':


        try:

            email = signupForm.emailField.data
            password = signupForm.passwordField.data
            name = signupForm.nameField.data
            repeatPassword = signupForm.password_confirm.data
            user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

            if user: # if a user is found, we want to redirect back to signup page so user can try again  
                flash('Email address already exists! Please login instead :)')
                return render_template("authy/signup.html",form=signupForm)

            if repeatPassword != password:
                flash('Passwords do not match!')
                repopSignupForm = SignupForm()
                repopSignupForm.emailField.data = signupForm.emailField.data
                repopSignupForm.nameField.data = signupForm.nameField.data
                return render_template("authy/signup.html",form=repopSignupForm)

            # create new user with the form data. Hash the password so plaintext version isn't saved.
            new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

            # add the new user to the database
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('dca.dcaSetup'))

        except:
            current_app.logger.exception("Could not signup user {}!".format(email))
            db.session.rollback()
            return redirect(url_for('main.index'))



@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
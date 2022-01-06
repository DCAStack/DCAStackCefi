from flask import render_template
from flask_login import login_required, current_user
from flask import current_app, request
from project.main import bp
from project.main.forms import ContactForm
from project.services.mailService import receive_contact_message

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/donate')
def donate():
    return render_template('donate.html')


@bp.route('/faq')
def faq():
    return render_template('faq.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():

    cform = ContactForm()

    if request.method == 'POST':
        userEmail = cform.emailField.data
        msgBody = cform.messageField.data
        msgSubject = cform.subjectField.data
        receive_contact_message(userEmail,msgSubject,msgBody)
        return render_template('contact_complete.html')

    return render_template('contact.html', form=cform)

    

@bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', name=current_user.name)
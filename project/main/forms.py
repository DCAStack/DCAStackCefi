
from flask_wtf import FlaskForm
from wtforms import StringField, validators, SubmitField, EmailField, SelectField, TextAreaField
  
  
class ContactForm(FlaskForm):
    emailField = EmailField('email', [validators.DataRequired("Please enter email!")])

    subjectFieldOptions = ["Bug Report", "Feature Request", "Connection Issues", "Exchange API Help","Other"]
    subjectField = SelectField('subject', choices=subjectFieldOptions, default=subjectFieldOptions[0])

    messageField = TextAreaField('message', [validators.DataRequired("Please enter a message!")])
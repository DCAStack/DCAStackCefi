from wtforms import SelectField, StringField, IntegerField, validators, EmailField, PasswordField, SubmitField
from flask_wtf import FlaskForm

class SignupForm(FlaskForm):
    
    emailField = EmailField('email', [validators.DataRequired("Please enter email!")])
    nameField = StringField('name', [validators.DataRequired("Please enter name!")])
    passwordField = PasswordField(label='password', validators=[
        validators.Length(min=6, max=20,message="Please enter password!"),
        validators.DataRequired("Please enter a password!")
    ])
    password_confirm = PasswordField(label='password_confirm', validators=[
        validators.Length(min=6, max=20, message="Please confirm password!"),
        validators.EqualTo('passwordField'),
        validators.DataRequired("Please confirm password!")
    ])

class LoginForm(FlaskForm):
    
    emailField = EmailField('email', [validators.DataRequired("Please enter email!")])
    passwordField = PasswordField(label='validators', validators=[
        validators.Length(min=6, max=20,message="Please enter password!"),
    ])
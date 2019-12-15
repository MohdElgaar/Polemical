from flask_wtf import FlaskForm
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User, Post, Comment

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddTopicForm(FlaskForm):
    name = StringField('What is your issue ?', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=140)])
    submit = SubmitField('ASK')

class RegisterationForm(FlaskForm):     
    username = StringField('Username', validators=[DataRequired(), Length(2, 64) ])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    re_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    
    

    

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about = TextAreaField('About me', validators=[Length(min=0, max=140)], default="Hello world!")
    submit = SubmitField('Submit')
   

    def __init__(self, current_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.current_username = current_username

    def validate_username(self, username):
        print("validation of username: ")
        if username.data != self.current_username.username:
            u = User.query.filter_by(username=username.data).first()
            if u:
                raise ValidationError("Username is already taken.")

class SearchForm(FlaskForm):
    search = StringField('Search_here',[DataRequired()])
    submit = SubmitField('Submit')
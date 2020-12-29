from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import IntegerField, SubmitField, StringField, DateField, SelectField, DecimalField
from wtforms.validators import DataRequired,ValidationError,NumberRange, Regexp
from wtforms.widgets import TextArea

from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length

class SigninForm(FlaskForm):
    userid = StringField('userid', validators=[InputRequired(), Length(min=1, max=20)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

class RegisterForm(FlaskForm):
    userid = StringField('userid', validators=[InputRequired(), Length(min=1, max=20)])
    name = StringField('name', validators=[InputRequired()])
    phone = StringField('phone', validators=[Length(min=10, max=10)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email')])
    aadhar = StringField('aadhar', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    repassword = PasswordField('repassword', validators=[InputRequired(), Length(min=8, max=80)])

class FilterForm(FlaskForm):
    type = IntegerField('type_id', validators=[InputRequired()])
    price = DecimalField('price', validators=[InputRequired()])
    checkin = DateField('checkin', validators=[InputRequired()])
    checkout = DateField('checkout', validators=[InputRequired()])

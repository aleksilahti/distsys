from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from app import User, Conv

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')

	submit = SubmitField('Login')

class RegisterForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

	submit = SubmitField('Sign Up')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('Username taken')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('An account with that email already exists')


class ConversationForm(FlaskForm):
	conv_name = StringField('Conversation name', validators=[DataRequired(), Length(min=8, max=30)])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

	submit = SubmitField('Create conversation')

	def validate_conversation(self, conv_name):
		conv = Conv.query.filter_by(conv_name=conv_name.data).first()
		if conv:
			raise ValidationError('Conversation with that name exists')

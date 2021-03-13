from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_mqtt import Mqtt
import os
import email_validator
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms import StringField, SubmitField, PasswordField, BooleanField

app = Flask("Conversation app")
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from flask_bcrypt import Bcrypt
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['MQTT_BROKER_URL'] = 'localhost' #test server at mosquitto
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'user'
app.config['MQTT_PASSWORD'] = 'secret'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    email = db.Column(db.String(256), nullable=False)
    pw_hash = db.Column(db.String(256), nullable=False)

    conversations = db.relationship("Conv", back_populates="user")

class Conv(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conv_name = db.Column(db.String(256), unique=True, nullable=False)
    pw_hash = db.Column(db.String(256), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))

    user = db.relationship("User", back_populates="conversations")

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

db.create_all()

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


# Home / Base URL
@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = ConversationForm()
    if form.validate_on_submit():
        # Hash the password and insert the conversation in SQLAlchemy db
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        print(str(current_user.id))
        conv = Conv(conv_name=form.conv_name.data, pw_hash=hashed_pw, user=User.query.get(int(current_user.id)))
        db.session.add(conv)
        db.session.commit()
        flash('Conversation created', 'success')
        return redirect(url_for('conversation', conv_name=conv.conv_name))
    return render_template('index.html', form=form)


# Login / Register
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.pw_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            session["user"] = user.id
            return redirect(url_for('home'))
        else:
            flash('Login Failed. Please Check Username and Password', 'error')
    return render_template('login.html', title='Login', form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        # Hash the password and insert the user in SQLAlchemy db
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, pw_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created: {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/conversations")
def conversations():
    if current_user.is_authenticated:
        all_conversations = Conv.query.all()
        return render_template('conversations.html', conversations=all_conversations)
    return redirect(url_for('login'))

@app.route("/conversation/<conv_name>", methods=["GET", "POST"])
def conversation(conv_name):
    if current_user.is_authenticated:
        conv = Conv.query.filter_by(conv_name=conv_name).first()
        mqtt.subscribe('conversations/' + conv_name)
        mqtt.publish('conversations/' + conv_name, 'weather,location=us-midwest temperature=82')
        return render_template('conversation.html', conv=conv)
    return redirect(url_for('login'))

# Toggle debug mode (run as "python3 app.py")
if __name__ == "__main__":
    app.run(debug=True)

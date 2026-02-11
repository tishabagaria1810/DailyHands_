"""
WTForms for DailyHands with CSRF Protection
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField, FloatField, DateField
from wtforms.validators import DataRequired, Email, Length, Regexp, ValidationError, Optional
import re

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp(r'[A-Z]', message='Password must contain at least 1 uppercase letter'),
        Regexp(r'[0-9]', message='Password must contain at least 1 number'),
        Regexp(r'[!@#$%^&*(),.?":{}|<>]', message='Password must contain at least 1 special character')
    ])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    city = StringField('City', validators=[DataRequired()])
    area = StringField('Area', validators=[Optional()])
    role = StringField('Role', validators=[DataRequired()])
    submit = SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    phone = StringField('Phone', validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()])
    submit = SubmitField('Send OTP')

class VerifyOTPForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify OTP')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp(r'[A-Z]', message='Password must contain at least 1 uppercase letter'),
        Regexp(r'[0-9]', message='Password must contain at least 1 number'),
        Regexp(r'[!@#$%^&*(),.?":{}|<>]', message='Password must contain at least 1 special character')
    ])
    submit = SubmitField('Reset Password')

class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    city = StringField('City', validators=[DataRequired()])
    area = StringField('Area', validators=[Optional()])
    submit = SubmitField('Update Profile')

class WorkRequestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    expected_duration = IntegerField('Expected Duration (days)', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    submit = SubmitField('Create Request')

class WorkerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    skill = StringField('Skill', validators=[DataRequired()])
    daily_wage = FloatField('Daily Wage', validators=[DataRequired()])
    submit = SubmitField('Add Worker')

class AttendanceForm(FlaskForm):
    worker_id = IntegerField('Worker ID', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Present', 'Present'), ('Absent', 'Absent')], validators=[DataRequired()])
    submit = SubmitField('Mark Attendance')

class RatingForm(FlaskForm):
    rating = IntegerField('Rating', validators=[DataRequired()])
    review = TextAreaField('Review', validators=[Optional()])
    submit = SubmitField('Submit Rating')

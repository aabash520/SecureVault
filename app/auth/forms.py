import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError


def strong_password(form, field):
    pw = field.data or ""
    if not re.search(r"[A-Z]", pw):
        raise ValidationError("Must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", pw):
        raise ValidationError("Must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", pw):
        raise ValidationError("Must contain at least one special character.")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=64),
            Regexp(r"^[A-Za-z0-9_.-]+$", message="Letters, digits, . _ - only."),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Master password",
        validators=[
            DataRequired(),
            Length(min=10, max=256, message="Master password must be at least 10 characters."),
            strong_password,
        ],
    )
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Master password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            Length(min=10, max=256),
            strong_password,
        ],
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Update password")

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    FloatField,
    IntegerField,
    HiddenField,
    SelectField,
)
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, ValidationError

from .models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Register")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")


class CardForm(FlaskForm):
    word = StringField("Word", validators=[DataRequired(), Length(max=120)])
    en_prefix = StringField("EN Prefix", validators=[DataRequired(), Length(max=255)])
    en_focus = StringField("EN Word", validators=[DataRequired(), Length(max=120)])
    en_suffix = StringField("EN Suffix", validators=[DataRequired(), Length(max=255)])
    en_translation = StringField("EN Translation", validators=[DataRequired(), Length(max=255)])

    ru_prefix = StringField("RU Prefix", validators=[DataRequired(), Length(max=255)])
    ru_focus = StringField("RU Word", validators=[DataRequired(), Length(max=120)])
    ru_suffix = StringField("RU Suffix", validators=[DataRequired(), Length(max=255)])
    ru_translation = StringField("RU Translation", validators=[DataRequired(), Length(max=255)])

    submit = SubmitField("Add Card")


class ExampleForm(FlaskForm):
    direction = SelectField(
        "Direction",
        choices=[("EN_RU", "EN → RU"), ("RU_EN", "RU → EN")],
        validators=[DataRequired()],
    )
    prefix = StringField("Prefix", validators=[DataRequired(), Length(max=255)])
    focus = StringField("Word", validators=[DataRequired(), Length(max=120)])
    suffix = StringField("Suffix", validators=[DataRequired(), Length(max=255)])
    translation = StringField("Translation", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("Save Example")


class SettingsForm(FlaskForm):
    interval_multiplier = FloatField(
        "Interval Multiplier", validators=[DataRequired(), NumberRange(min=1.0, max=10.0)]
    )
    initial_interval_minutes = IntegerField(
        "Initial Interval (minutes)", validators=[DataRequired(), NumberRange(min=1, max=1440)]
    )
    submit = SubmitField("Save Settings")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change Password")


class ReviewForm(FlaskForm):
    example_id = HiddenField(validators=[DataRequired()])
    answer = StringField("Answer", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("OK")


class ReviewContinueForm(FlaskForm):
    submit = SubmitField("Start New Repetition")

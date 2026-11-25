from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from ..extensions import db
from ..models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


class RegisterForm(FlaskForm):
    full_name = StringField("F.I.Sh.", validators=[DataRequired(), Length(min=3, max=120)])
    username = StringField("Foydalanuvchi nomi", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Parol", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Parolni tasdiqlang", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Ro‘yxatdan o‘tish")


class LoginForm(FlaskForm):
    username = StringField("Login yoki email", validators=[DataRequired()])
    password = PasswordField("Parol", validators=[DataRequired()])
    submit = SubmitField("Kirish")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
            flash("Bu login yoki email allaqachon ishlatilgan.", "danger")
        else:
            user = User(full_name=form.full_name.data, username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Ro‘yxatdan o‘tish muvaffaqiyatli. Endi kiring.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username.data) | (User.email == form.username.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.index"))
        flash("Login yoki parol noto‘g‘ri.", "danger")
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))

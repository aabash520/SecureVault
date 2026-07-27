import base64
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, login_required, current_user

from ..models import db, User
from ..crypto import derive_key, new_salt
from .. import limiter
from .forms import RegisterForm, LoginForm, ChangePasswordForm

auth_bp = Blueprint("auth", __name__)

MAX_FAILED_LOGINS = 5


def _stash_vault_key(key: bytes) -> None:
    session["vault_key"] = base64.b64encode(key).decode("ascii")
    session.permanent = True


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("vault.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already registered.", "error")
            return render_template("auth/register.html", form=form)

        user = User(username=username, email=email, key_salt=new_salt())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("vault.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user is None or user.failed_logins >= MAX_FAILED_LOGINS:
            flash("Invalid credentials or account temporarily locked.", "error")
            return render_template("auth/login.html", form=form)

        if not user.check_password(form.password.data):
            user.failed_logins += 1
            db.session.commit()
            flash("Invalid credentials.", "error")
            return render_template("auth/login.html", form=form)

        user.failed_logins = 0
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        key = derive_key(form.password.data, user.key_salt)
        _stash_vault_key(key)
        login_user(user)
        return redirect(url_for("vault.dashboard"))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.pop("vault_key", None)
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "error")
            return render_template("auth/settings.html", form=form)
        current_user.set_password(form.new_password.data)
        new_key = derive_key(form.new_password.data, current_user.key_salt)
        _stash_vault_key(new_key)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("auth.settings"))
    return render_template("auth/settings.html", form=form)


@auth_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    password = request.form.get("password", "")
    if not current_user.check_password(password):
        flash("Incorrect password. Account not deleted.", "error")
        return redirect(url_for("auth.settings"))
    session.clear()
    db.session.delete(current_user)
    db.session.commit()
    flash("Your account and all vault data have been permanently deleted.", "success")
    return redirect(url_for("main.index"))

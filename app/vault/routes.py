import base64
import secrets
import string
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort, session, jsonify
)
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from flask_login import login_required, current_user

from ..models import db, VaultEntry, ENTRY_CATEGORIES
from ..crypto import encrypt, decrypt

vault_bp = Blueprint("vault", __name__)

_CATEGORY_CHOICES = [(c, c) for c in ENTRY_CATEGORIES]


class EntryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    category = SelectField("Category", choices=_CATEGORY_CHOICES, default="Login")
    site_url = StringField("Website URL", validators=[Optional(), Length(max=255)])
    username = StringField("Username / email", validators=[Optional(), Length(max=255)])
    secret = StringField("Password / secret", validators=[DataRequired(), Length(max=2048)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=4096)])
    submit = SubmitField("Save")


def _get_key() -> bytes:
    b64 = session.get("vault_key")
    if not b64:
        abort(401)
    return base64.b64decode(b64)


@vault_bp.route("/")
@login_required
def dashboard():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "").strip()
    favorites = request.args.get("favorites", "").strip()
    query = VaultEntry.query.filter_by(user_id=current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (VaultEntry.title.ilike(like))
            | (VaultEntry.site_url.ilike(like))
            | (VaultEntry.username.ilike(like))
        )
    if cat and cat in ENTRY_CATEGORIES:
        query = query.filter_by(category=cat)
    if favorites:
        query = query.filter_by(is_favorite=True)
    entries = query.order_by(VaultEntry.is_favorite.desc(), VaultEntry.updated_at.desc()).all()
    return render_template(
        "vault/dashboard.html",
        entries=entries, q=q, cat=cat,
        categories=ENTRY_CATEGORIES, favorites=favorites,
    )


@vault_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = EntryForm()
    if form.validate_on_submit():
        key = _get_key()
        entry = VaultEntry(
            user_id=current_user.id,
            title=form.title.data.strip(),
            category=form.category.data,
            site_url=(form.site_url.data or "").strip() or None,
            username=(form.username.data or "").strip() or None,
            secret_ciphertext=encrypt(key, form.secret.data),
            notes_ciphertext=encrypt(key, form.notes.data) if form.notes.data else None,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Entry saved.", "success")
        return redirect(url_for("vault.dashboard"))
    return render_template("vault/entry_form.html", form=form, mode="Create")


@vault_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit(entry_id):
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    key = _get_key()
    form = EntryForm()
    if request.method == "GET":
        form.title.data = entry.title
        form.category.data = entry.category
        form.site_url.data = entry.site_url
        form.username.data = entry.username
        form.secret.data = decrypt(key, entry.secret_ciphertext)
        form.notes.data = decrypt(key, entry.notes_ciphertext) if entry.notes_ciphertext else ""
    if form.validate_on_submit():
        entry.title = form.title.data.strip()
        entry.category = form.category.data
        entry.site_url = (form.site_url.data or "").strip() or None
        entry.username = (form.username.data or "").strip() or None
        entry.secret_ciphertext = encrypt(key, form.secret.data)
        entry.notes_ciphertext = encrypt(key, form.notes.data) if form.notes.data else None
        db.session.commit()
        flash("Entry updated.", "success")
        return redirect(url_for("vault.dashboard"))
    return render_template("vault/entry_form.html", form=form, mode="Edit")


@vault_bp.route("/<int:entry_id>/reveal", methods=["POST"])
@login_required
def reveal(entry_id):
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    key = _get_key()
    return jsonify(
        {
            "secret": decrypt(key, entry.secret_ciphertext),
            "notes": decrypt(key, entry.notes_ciphertext) if entry.notes_ciphertext else "",
        }
    )


@vault_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete(entry_id):
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted.", "success")
    return redirect(url_for("vault.dashboard"))


@vault_bp.route("/<int:entry_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(entry_id):
    entry = VaultEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    entry.is_favorite = not entry.is_favorite
    db.session.commit()
    return jsonify({"is_favorite": entry.is_favorite})


@vault_bp.route("/export")
@login_required
def export_vault():
    key = _get_key()
    entries = VaultEntry.query.filter_by(user_id=current_user.id).all()
    data = []
    for e in entries:
        data.append({
            "id": e.id,
            "title": e.title,
            "category": e.category,
            "site_url": e.site_url,
            "username": e.username,
            "secret": decrypt(key, e.secret_ciphertext),
            "notes": decrypt(key, e.notes_ciphertext) if e.notes_ciphertext else "",
            "is_favorite": e.is_favorite,
            "created_at": e.created_at.isoformat(),
            "updated_at": e.updated_at.isoformat(),
        })
    response = jsonify({"vault_export": data, "entry_count": len(data)})
    response.headers["Content-Disposition"] = "attachment; filename=securevault_export.json"
    return response


@vault_bp.route("/generate-password")
@login_required
def generate_password():
    length = min(int(request.args.get("length", 20)), 64)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        has_upper = any(c.isupper() for c in pw)
        has_digit = any(c.isdigit() for c in pw)
        has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in pw)
        if has_upper and has_digit and has_special:
            break
    return jsonify({"password": pw})

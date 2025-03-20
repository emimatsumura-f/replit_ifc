from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from . import db, login_manager
from .models import User
from .forms import LoginForm, RegistrationForm
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(id):
    logger.debug(f"Loading user with ID: {id}")
    user = User.query.get(int(id))
    logger.debug(f"User found: {user is not None}")
    return user

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('ifc.index'))

    form = LoginForm()
    if form.validate_on_submit():
        logger.debug(f"Login attempt for email: {form.email.data}")
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            logger.debug("Invalid login attempt")
            flash('メールアドレスまたはパスワードが正しくありません', 'error')
            return redirect(url_for('auth.login'))

        login_user(user)
        logger.debug(f"Successful login for user: {user.username}")
        flash('ログインしました', 'success')
        # ログイン後はifc.indexにリダイレクト
        return redirect(url_for('ifc.index'))

    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('ifc.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            logger.debug(f"Attempting to register new user: {form.username.data}")
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            logger.debug(f"Successfully registered user: {user.username}")
            flash('登録が完了しました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            db.session.rollback()
            flash('登録中にエラーが発生しました。', 'error')

    return render_template('auth/signup.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました', 'success')
    return redirect(url_for('auth.login'))
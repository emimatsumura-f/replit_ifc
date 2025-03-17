import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import csv
import tempfile
from ifc_processor import process_ifc_file

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
# セッション管理のための固定キーを設定
app.secret_key = "your-secret-key-here"

# データベース設定
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ifc_converter.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 最大ファイルサイズ: 16MB
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()

# LoginManagerの設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'この機能を使用するにはログインが必要です。'

# アップロード可能なファイル拡張子
ALLOWED_EXTENSIONS = {"ifc"}

db.init_app(app)

# モデルとフォームのインポート
from models import User, UploadHistory
from forms import LoginForm, RegistrationForm

@login_manager.user_loader
def load_user(id):
    logger.debug(f"Loading user with ID: {id}")
    user = User.query.get(int(id))
    logger.debug(f"User found: {user is not None}")
    return user

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        logger.debug(f"Login attempt for email: {form.email.data}")
        user = User.query.filter_by(email=form.email.data).first()

        if user is None:
            logger.debug("User not found")
            flash("メールアドレスまたはパスワードが正しくありません", "error")
            return redirect(url_for("login"))

        if not user.check_password(form.password.data):
            logger.debug("Invalid password")
            flash("メールアドレスまたはパスワードが正しくありません", "error")
            return redirect(url_for("login"))

        logger.debug(f"Successful login for user: {user.username}")
        login_user(user)
        flash("ログインしました", "success")
        return redirect(url_for("index"))

    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            logger.debug(f"Attempting to register new user: {form.username.data}, {form.email.data}")
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            logger.debug(f"Successfully registered user: {user.username}")
            flash("登録が完了しました。ログインしてください。", "success")
            return redirect(url_for("login"))
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            db.session.rollback()
            flash("登録中にエラーが発生しました。", "error")

    return render_template("register.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash("ログアウトしました", "success")
    return redirect(url_for("login"))

@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            elements = process_ifc_file(filepath)

            # 履歴に保存
            history = UploadHistory(
                filename=filename,
                processed_date=datetime.now(),
                element_count=len(elements),
                user_id=current_user.id,
                processed_data=json.dumps(elements)
            )
            db.session.add(history)
            db.session.commit()

            # 一時ファイルを削除
            os.remove(filepath)

            return redirect(url_for('preview', upload_id=history.id))

        except Exception as e:
            logger.error(f"ファイル処理エラー: {str(e)}")
            flash(f"ファイルの処理中にエラーが発生しました: {str(e)}", "error")
            return redirect(url_for("index"))
    else:
        flash("無効なファイル形式です。IFCファイルをアップロードしてください。", "error")
        return redirect(url_for("index"))

@app.route("/preview/<int:upload_id>")
@login_required
def preview(upload_id):
    upload = UploadHistory.query.get_or_404(upload_id)
    if upload.user_id != current_user.id:
        flash("アクセス権限がありません", "error")
        return redirect(url_for("index"))
    elements = json.loads(upload.processed_data)
    return render_template("preview.html", upload=upload, elements=elements)

@app.route("/download/<int:upload_id>")
@login_required
def download_csv(upload_id):
    upload = UploadHistory.query.get_or_404(upload_id)
    if upload.user_id != current_user.id:
        flash("アクセス権限がありません", "error")
        return redirect(url_for("index"))

    elements = json.loads(upload.processed_data)
    csv_filename = f"部材リスト_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(app.config["UPLOAD_FOLDER"], csv_filename)

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["部材種別", "サイズ", "重量", "長さ", "数量"])
        for element in elements:
            writer.writerow([
                element["type"],
                element["size"],
                element["weight"],
                element["length"],
                element["quantity"]
            ])

    return send_file(
        csv_path,
        as_attachment=True,
        download_name=csv_filename,
        mimetype='text/csv'
    )

@app.route("/history")
@login_required
def history():
    uploads = UploadHistory.query.filter_by(user_id=current_user.id).order_by(UploadHistory.processed_date.desc()).all()
    return render_template("history.html", uploads=uploads)

with app.app_context():
    # データベースを再作成
    logger.info("Recreating database tables...")
    db.drop_all()
    db.create_all()
    logger.info("Database tables created successfully")
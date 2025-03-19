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

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# データベース設定
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 最大ファイルサイズ: 100MB
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", tempfile.gettempdir()) # Fallback to tempdir if env var not set

# LoginManagerの設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'この機能を使用するにはログインが必要です。'

# アップロード可能なファイル拡張子
ALLOWED_EXTENSIONS = {"ifc"}

# データベースの初期化
db.init_app(app)

# モデルとフォームのインポート
from models import User, UploadHistory
from forms import LoginForm, RegistrationForm

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("upload"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("メールアドレスまたはパスワードが正しくありません", "error")
            return redirect(url_for("login"))

        login_user(user)
        flash("ログインしました", "success")
        return redirect(url_for("upload"))

    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("upload"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
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

@app.route("/upload")
@login_required
def upload():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("upload"))

    file = request.files["file"]
    if file.filename == "":
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("upload"))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            from ifc_processor import process_ifc_file
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
            return redirect(url_for("upload"))
    else:
        flash("無効なファイル形式です。IFCファイルをアップロードしてください。", "error")
        return redirect(url_for("upload"))

@app.route("/preview/<int:upload_id>")
@login_required
def preview(upload_id):
    upload = UploadHistory.query.get_or_404(upload_id)
    if upload.user_id != current_user.id:
        flash("アクセス権限がありません", "error")
        return redirect(url_for("upload"))
    elements = json.loads(upload.processed_data)
    return render_template("preview.html", upload=upload, elements=elements)

@app.route("/download/<int:upload_id>")
@login_required
def download_csv(upload_id):
    upload = UploadHistory.query.get_or_404(upload_id)
    if upload.user_id != current_user.id:
        flash("アクセス権限がありません", "error")
        return redirect(url_for("upload"))

    elements = json.loads(upload.processed_data)
    csv_filename = f"部材リスト_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(app.config["UPLOAD_FOLDER"], csv_filename)

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["部材種別", "部材名", "断面性能", "重量", "長さ"])
        for element in elements:
            writer.writerow([
                element["type"],
                element["name"],
                element["size"],
                element["weight"],
                element["length"]
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

# データベースの作成
with app.app_context():
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database initialization completed")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
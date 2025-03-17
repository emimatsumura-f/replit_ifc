import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
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
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# SQLiteデータベースの設定
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ifc_converter.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 最大ファイルサイズ: 16MB
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()

# アップロード可能なファイル拡張子
ALLOWED_EXTENSIONS = {"ifc"}

db.init_app(app)

# モデルのインポート（db初期化後に行う）
from models import UploadHistory

def allowed_file(filename):
    """
    アップロードされたファイルの拡張子が許可されているかチェック
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """
    ホームページを表示
    """
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    IFCファイルをアップロードして処理する
    """
    if "file" not in request.files:
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        try:
            # ファイル名を安全に保存
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # IFCファイルを処理
            elements = process_ifc_file(filepath)

            # CSV出力ファイル名を生成
            csv_filename = f"部材リスト_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(app.config["UPLOAD_FOLDER"], csv_filename)

            # CSV作成
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

            # 履歴に保存
            history = UploadHistory(
                filename=filename,
                processed_date=datetime.now(),
                element_count=len(elements)
            )
            db.session.add(history)
            db.session.commit()

            # 一時ファイルを削除
            os.remove(filepath)

            return send_file(
                csv_path,
                as_attachment=True,
                download_name=csv_filename,
                mimetype='text/csv'
            )

        except Exception as e:
            logger.error(f"ファイル処理エラー: {str(e)}")
            flash(f"ファイルの処理中にエラーが発生しました: {str(e)}", "error")
            return redirect(url_for("index"))
    else:
        flash("無効なファイル形式です。IFCファイルをアップロードしてください。", "error")
        return redirect(url_for("index"))

@app.route("/history")
def history():
    """
    変換履歴を表示
    """
    uploads = UploadHistory.query.order_by(UploadHistory.processed_date.desc()).all()
    return render_template("history.html", uploads=uploads)

with app.app_context():
    db.create_all()
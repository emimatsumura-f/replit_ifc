import os
import json
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from . import db
from .models import UploadHistory
from .utils.ifc_parser import process_ifc_file
from .utils.csv_generator import generate_csv, generate_csv_filename
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('ifc', __name__)

def allowed_file(filename):
    """アップロード可能なファイル拡張子をチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'ifc'

@bp.route('/')
@login_required
def index():
    return render_template('ifc/upload.html')

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('ファイルが選択されていません', 'error')
        return redirect(url_for('ifc.index'))

    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません', 'error')
        return redirect(url_for('ifc.index'))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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

            return redirect(url_for('ifc.preview', upload_id=history.id))

        except Exception as e:
            logger.error(f"ファイル処理エラー: {str(e)}")
            flash(f"ファイルの処理中にエラーが発生しました: {str(e)}", 'error')
            return redirect(url_for('ifc.index'))
    else:
        flash('無効なファイル形式です。IFCファイルをアップロードしてください。', 'error')
        return redirect(url_for('ifc.index'))

@bp.route('/preview/<int:upload_id>')
@login_required
def preview(upload_id):
    upload = UploadHistory.query.get_or_404(upload_id)
    if upload.user_id != current_user.id:
        flash('アクセス権限がありません', 'error')
        return redirect(url_for('ifc.index'))
    elements = json.loads(upload.processed_data)
    return render_template('ifc/preview.html', upload=upload, elements=elements)

@bp.route('/download/<int:upload_id>')
@login_required
def download_csv(upload_id):
    upload = UploadHistory.query.get_or_404(upload_id)
    if upload.user_id != current_user.id:
        flash('アクセス権限がありません', 'error')
        return redirect(url_for('ifc.index'))

    elements = json.loads(upload.processed_data)
    csv_filename = generate_csv_filename()
    csv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], csv_filename)

    generate_csv(elements, csv_path)

    return send_file(
        csv_path,
        as_attachment=True,
        download_name=csv_filename,
        mimetype='text/csv'
    )

@bp.route('/history')
@login_required
def history():
    uploads = UploadHistory.query.filter_by(user_id=current_user.id)\
        .order_by(UploadHistory.processed_date.desc()).all()
    return render_template('ifc/history.html', uploads=uploads)
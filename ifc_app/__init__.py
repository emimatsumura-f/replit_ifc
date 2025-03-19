import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'この機能を使用するにはログインが必要です。'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # アップロードディレクトリの作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 拡張機能の初期化
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # ブループリントの登録
        from ifc_app.auth import bp as auth_bp
        app.register_blueprint(auth_bp)

        from ifc_app.ifc_processor import bp as ifc_bp
        app.register_blueprint(ifc_bp)

        # データベースの初期化
        db.create_all()

    return app

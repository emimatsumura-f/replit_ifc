import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# データベースインスタンスの作成
from .db import db

# LoginManagerの設定
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'この機能を使用するにはログインが必要です。'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 設定情報のログ出力
    logger.debug(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.debug(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    logger.debug(f"Instance path: {app.instance_path}")

    # アップロードディレクトリの作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # データベースの初期化
    db.init_app(app)

    # LoginManagerの初期化
    login_manager.init_app(app)

    with app.app_context():
        # ブループリントの登録
        from .auth import bp as auth_bp
        app.register_blueprint(auth_bp)

        from .ifc_processor import bp as ifc_bp
        app.register_blueprint(ifc_bp)

        # モデルのインポート（create_all()の前に必要）
        from . import models

        # データベースの作成
        logger.info("Creating database tables...")
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    return app
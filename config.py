import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DATABASE_PATH = os.path.join(INSTANCE_DIR, 'ifc_converter.db')

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{DATABASE_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

    # 必要なディレクトリを作成
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/ifc_converter.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

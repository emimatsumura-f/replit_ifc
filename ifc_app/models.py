from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
from .db import db

logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        logger.debug(f"Password hash created for user {self.username}")

    def check_password(self, password):
        result = check_password_hash(self.password_hash, password)
        logger.debug(f"Password check for user {self.username}: {'success' if result else 'failed'}")
        return result

    def __repr__(self):
        return f'<User {self.username}>'

class UploadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    processed_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    element_count = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    processed_data = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<UploadHistory {self.filename}>'

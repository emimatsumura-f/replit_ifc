from app import db
from datetime import datetime

class UploadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    processed_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    element_count = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<UploadHistory {self.filename}>'

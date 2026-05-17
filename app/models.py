from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    contents = db.relationship('Content', backref='user', lazy=True, cascade='all, delete-orphan')

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)   # text, photo, video, link
    content = db.Column(db.Text)                     # текст или URL
    file_id = db.Column(db.String(200))              # Telegram file_id (для фото/видео)
    local_path = db.Column(db.String(500))           # относительный путь для веба
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
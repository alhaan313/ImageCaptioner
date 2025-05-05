from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    endpoint = db.Column(db.String(100))
    ip_address = db.Column(db.String(100))
    user_agent = db.Column(db.String(200))
    image_processed = db.Column(db.Boolean, default=False)

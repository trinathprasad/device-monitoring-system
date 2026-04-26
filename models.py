from extensions import db
from datetime import datetime,timezone

class DeviceData(db.Model):
    __tablename__ = 'device_data'

    id = db.Column(db.Integer, primary_key=True)
    cpu = db.Column(db.Float)
    memory = db.Column(db.Float)
    uptime = db.Column(db.Float)
    battery = db.Column(db.Float)
    status = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
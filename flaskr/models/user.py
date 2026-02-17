from flask_login import UserMixin
from flaskr import db
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    mailaddress = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    profile = db.Column(db.String, nullable=True)

    # Relationships
    posted_debates = db.relationship('Debate', foreign_keys='Debate.poster_id', back_populates='poster', lazy=True)
    challenged_debates = db.relationship('Debate', foreign_keys='Debate.challenger_id', back_populates='challenger', lazy=True)
    exchanges = db.relationship('Exchange', back_populates='sender', lazy=True)
    votes = db.relationship('Vote', back_populates='voter', lazy=True)
    comments = db.relationship('Comment', back_populates='poster', lazy=True)
    notifications = db.relationship('Notification', back_populates='user', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f'<User {self.username}>'

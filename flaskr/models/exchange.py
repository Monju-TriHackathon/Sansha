from flaskr import db
from datetime import datetime, timezone


class Exchange(db.Model):
    __tablename__ = 'exchanges'

    exchange_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.debate_id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message = db.Column(db.String, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    turn_number = db.Column(db.Integer, nullable=True)

    # Relationships
    debate = db.relationship('Debate', back_populates='exchanges')
    sender = db.relationship('User', back_populates='exchanges')

    def __repr__(self):
        return f'<Exchange {self.exchange_id}>'

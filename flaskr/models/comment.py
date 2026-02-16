from flaskr import db
from datetime import datetime, timezone


class Comment(db.Model):
    __tablename__ = 'comments'

    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.debate_id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    comment = db.Column(db.String, nullable=False)
    posted_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    debate = db.relationship('Debate', back_populates='comments')
    poster = db.relationship('User', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.comment_id}>'

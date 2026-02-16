from flaskr import db
from datetime import datetime, timezone


class Vote(db.Model):
    __tablename__ = 'votes'

    vote_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.debate_id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    voting_destination = db.Column(db.Integer, nullable=False, comment='poster(0)/challenger(1)')
    voted_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # 同一ユーザが同一議題に重複投票不可
    __table_args__ = (
        db.UniqueConstraint('debate_id', 'voter_id', name='uq_votes_debate_voter'),
    )

    # Relationships
    debate = db.relationship('Debate', back_populates='votes')
    voter = db.relationship('User', back_populates='votes')

    def __repr__(self):
        return f'<Vote {self.vote_id}>'

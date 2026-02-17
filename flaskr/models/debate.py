from flaskr import db
from datetime import datetime, timezone


class Debate(db.Model):
    __tablename__ = 'debates'

    # 基本情報
    debate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    challenger_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 現状態
    state = db.Column(db.Integer, nullable=False, default=0, comment='open(0)/in_debate(1)/voting(2)/closed(3)')
    current_turn = db.Column(db.Integer, nullable=True)
    current_speaker = db.Column(db.Integer, nullable=True, comment='poster(0)/challenger(1)')
    outcome = db.Column(db.Integer, nullable=True, comment='poster_win(0)/challenger_win(1)/draw(2)')
    current_speaker_started_at = db.Column(db.DateTime, nullable=True)
    finish_reason = db.Column(db.Integer, nullable=True, comment='normal(0)/no_show(1)/time_out(2)')
    debate_start_time = db.Column(db.DateTime, nullable=True)
    voting_start_time = db.Column(db.DateTime, nullable=True)
    current_number_of_votes = db.Column(db.Integer, nullable=False, default=0)

    # 議論設定
    method = db.Column(db.Integer, nullable=False, comment='turn(0)/realtime(1)', default=0)
    max_number_of_votes = db.Column(db.Integer, nullable=False, default=100)
    max_turns = db.Column(db.Integer, nullable=True)
    challenger_waiting_period_minutes = db.Column(db.Integer, nullable=False, default=2880)
    debate_period_minutes = db.Column(db.Integer, nullable=False, default=1440)
    voting_period_minutes = db.Column(db.Integer, nullable=False, default=1440)
    turn_time_limit_minutes = db.Column(db.Integer, nullable=True)

    # Relationships
    poster = db.relationship('User', foreign_keys=[poster_id], back_populates='posted_debates')
    challenger = db.relationship('User', foreign_keys=[challenger_id], back_populates='challenged_debates')
    exchanges = db.relationship('Exchange', back_populates='debate', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', back_populates='debate', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='debate', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='debate_tags', back_populates='debates', lazy=True)

    # 許可されるソート基準のセット
    ALLOWED_SORT_COLUMNS = {'created_at', 'updated_at', 'current_number_of_votes'}

    def __repr__(self):
        return f'<Debate {self.title}>'

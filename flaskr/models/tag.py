from flaskr import db


class Tag(db.Model):
    __tablename__ = 'tags'

    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String, unique=True, nullable=False)

    # Relationships
    debates = db.relationship('Debate', secondary='debate_tags', back_populates='tags', lazy=True)

    def __repr__(self):
        return f'<Tag {self.tag_name}>'

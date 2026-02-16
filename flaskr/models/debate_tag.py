from flaskr import db


class DebateTag(db.Model):
    __tablename__ = 'debate_tags'

    debate_id = db.Column(db.Integer, db.ForeignKey('debates.debate_id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), primary_key=True)

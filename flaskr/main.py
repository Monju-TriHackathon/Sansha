from flask import render_template, Blueprint

bp = Blueprint('app', __name__)

@bp.route('/')
def index():
    return render_template('base.html')

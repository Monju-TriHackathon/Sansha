from flask import render_template, Blueprint, redirect, url_for
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('debate.get_debates'))
    return render_template('login.html')

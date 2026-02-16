from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.models.user import User
from flaskr import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mailaddress = request.form['mailaddress']
        error = None

        # バリデーション
        if not username:
            error = 'ユーザー名は必須です'
        elif not password:
            error = 'パスワードは必須です'
        elif not mailaddress:
            error = 'メールアドレスは必須です'

        # ユーザー名の重複チェック
        if error is None:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user is not None:
                error = f'ユーザー名 {username} は既に登録されています'

        # メールアドレスの重複チェック
        if error is None:
            existing_mail = User.query.filter_by(mailaddress=mailaddress).first()
            if existing_mail is not None:
                error = 'このメールアドレスは既に登録されています'

        if error is None:
            try:
                # 新規ユーザーを作成
                new_user = User(
                    username=username,
                    password=generate_password_hash(password),
                    mailaddress=mailaddress
                )
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('auth.login'))
            except Exception:
                db.session.rollback()
                error = '登録に失敗しました。もう一度お試しください'

        flash(error)

    return render_template('register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'ユーザー名が正しくありません'
        elif not check_password_hash(user.password, password):
            error = 'パスワードが正しくありません'

        if error is None:
            session.clear()
            session['user_id'] = user.user_id
            return redirect(url_for('main.index'))

        flash(error)

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))
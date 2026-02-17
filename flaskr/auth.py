from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.models.user import User
from flaskr import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    """
    アカウント登録を処理する

    GET: 登録フォームを表示
    POST: 入力データのバリデーションとユーザー作成を行う

    フォームパラメータ:
        username (str): ユーザー名（必須・一意）
        password (str): パスワード（必須）
        mailaddress (str): メールアドレス（必須・一意）

    Returns:
        GET: register.html テンプレート
        POST（成功）: ログインページへリダイレクト
        POST（失敗）: エラーメッセージと共に register.html を再表示
    """
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
    """
    ログインを処理する

    GET: ログインフォームを表示
    POST: ユーザー認証を行い、セッションを開始する

    フォームパラメータ:
        username (str): ユーザー名
        password (str): パスワード

    Returns:
        GET: login.html テンプレート
        POST（成功）: トップページへリダイレクト
        POST（失敗）: エラーメッセージと共に login.html を再表示
    """
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
            login_user(user)
            return redirect(url_for('main.index'))

        flash(error)

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    """
    ログアウトを処理する

    ログイン済みユーザーのセッションを終了し、トップページへリダイレクトする

    Returns:
        トップページへリダイレクト
    """
    logout_user()
    return redirect(url_for('main.index'))
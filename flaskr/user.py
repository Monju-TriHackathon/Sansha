from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from flaskr.models.user import User
from flaskr import db

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/<int:user_id>')
def get_profile(user_id):
    """
    ユーザープロフィールを取得する

    指定されたuser_idのユーザー情報をデータベースから取得し、表示する

    パラメータ:
        user_id (int): 取得対象のユーザーID

    Returns:
        profile.html テンプレート（ユーザー情報を含む）
        ユーザーが存在しない場合: 404エラー
    """
    user = db.session.get(User, user_id)
    if user is None:
        return render_template('404.html'), 404

    return render_template('profile.html', user=user)


@bp.route('/edit', methods=('GET', 'POST'))
@login_required
def update_profile():
    """
    ユーザープロフィールを更新する

    GET: プロフィール編集フォームを表示
    POST: 入力データのバリデーションとプロフィール更新を行う

    フォームパラメータ:
        username (str): ユーザー名（必須・一意）
        mailaddress (str): メールアドレス（必須・一意）
        profile (str): プロフィール（任意）
        password (str): 新しいパスワード（任意・入力時のみ更新）

    Returns:
        GET: edit_profile.html テンプレート
        POST（成功）: プロフィールページへリダイレクト
        POST（失敗）: エラーメッセージと共に edit_profile.html を再表示
    """
    if request.method == 'POST':
        username = request.form['username']
        mailaddress = request.form['mailaddress']
        profile = request.form.get('profile', '')
        password = request.form.get('password', '')
        error = None

        # バリデーション
        if not username:
            error = 'ユーザー名は必須です'
        elif not mailaddress:
            error = 'メールアドレスは必須です'

        # ユーザー名の重複チェック（自分以外）
        if error is None:
            existing_user = User.query.filter(
                User.username == username,
                User.user_id != current_user.user_id
            ).first()
            if existing_user is not None:
                error = f'ユーザー名 {username} は既に使用されています'

        # メールアドレスの重複チェック（自分以外）
        if error is None:
            existing_mail = User.query.filter(
                User.mailaddress == mailaddress,
                User.user_id != current_user.user_id
            ).first()
            if existing_mail is not None:
                error = 'このメールアドレスは既に使用されています'

        if error is None:
            try:
                # 更新内容を反映
                current_user.username = username
                current_user.mailaddress = mailaddress
                current_user.profile = profile

                # パスワードが入力された場合のみ更新（ハッシュ化）
                if password:
                    current_user.password = generate_password_hash(password)

                db.session.commit()
                flash('プロフィールを更新しました')
                return redirect(url_for('user.get_profile', user_id=current_user.user_id))
            except Exception:
                db.session.rollback()
                error = '更新に失敗しました。もう一度お試しください'

        flash(error)

    return render_template('edit_profile.html', user=current_user)

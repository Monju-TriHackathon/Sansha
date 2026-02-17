from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from flaskr.models.notification import Notification
from flaskr import db

bp = Blueprint('notification', __name__, url_prefix='/notification')

# 1回のリクエストで取得する通知件数
PER_PAGE = 10


@bp.route('/')
@login_required
def get_notifications():
    """
    通知一覧を取得する

    ログイン中のユーザーの通知を新しい順に取得する
    無限スクロール対応のため、pageパラメータで件数制限を行う

    クエリパラメータ:
        page (int): ページ番号（デフォルト: 1）

    Returns:
        notifications.html テンプレート（通知一覧を含む）
    """
    page = request.args.get('page', 1, type=int)

    # 通知を新しい順に取得（件数制限あり）
    notifications = Notification.query.filter_by(
        user_id=current_user.user_id
    ).order_by(
        Notification.created_at.desc()
    ).offset(
        (page - 1) * PER_PAGE
    ).limit(
        PER_PAGE
    ).all()

    # 次のページが存在するかの判定
    has_next = len(notifications) == PER_PAGE

    return render_template(
        'notifications.html',
        notifications=notifications,
        page=page,
        has_next=has_next
    )

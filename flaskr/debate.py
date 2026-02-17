from threading import current_thread
from flask import Blueprint, flash, request, render_template, url_for, redirect
from flaskr import db
from flaskr.models import Debate, Tag, DebateTag
from flask_login import login_required, current_user

bp = Blueprint('debate', __name__)

DEFAULT_SETTINGS = {
    'title': '',  # タイトルは必須
    'description': '',  # 説明は必須
    'method': 0,  # デフォルトの議論方法はturn
    'max_number_of_votes': 100,  # デフォルトの最大投票数
    'max_turns': 10,  # デフォルトの最大ターン数(リアルタイム議論の場合は無効)
    'challenger_waiting_period_minutes': 120,  # デフォルトの挑戦者待機時間(2時間)
    'debate_period_minutes': 1440,  # デフォルトの議論期間(24時間)
    'voting_period_minutes': 1440,  # デフォルトの投票期間(24時間)
    'turn_time_limit_minutes': 30,  # デフォルトのターン時間制限(30分、ターン制議論の場合のみ有効)
}

@bp.route('/debates', methods=['GET'])
def get_debates():
    """
    議論の一覧を取得する
    クエリパラメータでタグを指定することで、特定のタグに関連する議論をフィルタリングして取得することも可能
    例: /debates?tag=technology&tag=education

    Returns:
        議論のリストを含むHTMLページ
    """
    # クエリパラメータからタグ、ソート基準、ソート順を取得
    tags = request.args.getlist('tag')  # タグ(tag_name)を取得
    sort_by = request.args.get('sorted', type=str)  # ソート基準を取得(デフォルトは作成日時)
    order = request.args.get('order', type=str)  # ソート順を取得(デフォルトは降順)

    # クエリを構築
    query = Debate.query

    # タグでフィルタリング
    if tags:
        # debate_tagsテーブルを使用して、指定されたタグに関連する議論をフィルタリング
        query = query.join(DebateTag).join(Tag).filter(Tag.tag_name.in_(tags))

    # ソート基準と順序を適用
    if sort_by in Debate.ALLOWED_SORT_COLUMNS:
        sort_column = getattr(Debate, sort_by)
        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        # デフォルトのソート基準を適用
        query = query.order_by(Debate.created_at.desc())

    # クエリを実行して議論のリストを取得
    debates = query.all()

    return render_template('debates.html', debates=debates)

@bp.route('/debates/<int:debate_id>', methods=['GET'])
def get_debate(debate_id):
    """
    特定の議論の詳細を取得する

    Args:
        debate_id (int): 取得する議論のID

    Returns:
        議論の詳細を含むHTMLページ
    """
    debate = Debate.query.get_or_404(debate_id)

    return render_template('debate_detail.html', debate=debate)

@bp.route('/debates/create', methods=['GET', 'POST'])
@login_required  # ログイン必須
def create_debate():
    """
    新しい議論を作成する
    POSTリクエストで必要な情報を受け取り、データベースに新しい議論を保存する

    Returns:
        GETリクエストの場合は議論作成フォームを含むHTMLページ
        POSTリクエストの場合は作成された議論の詳細ページにリダイレクト
    """
    poster_id = current_user.user_id  # ログインユーザーのIDを投稿者IDとして使用

    if request.method == 'POST':
        params = {
            key: request.form.get(key, default=val, type=type(val))
            for key, val in DEFAULT_SETTINGS.items()
        }

        # バリデーション: タイトル、説明、投稿者IDは必須
        title_len = len(params['title'].strip())
        description_len = len(params['description'].strip())

        if title_len == 0 or description_len == 0:
            flash('タイトルと説明は必須です。', 'error')
            return render_template('create_debate.html'), 400

        # バリデーション: 議論方法によって、最大ターン数とターン時間制限の必須/無効をチェック
        if params['method'] == 0:  # ターン制議論の場合
            if params['max_turns'] is None or params['turn_time_limit_minutes'] is None:
                flash('ターン制議論の場合、最大ターン数とターン時間制限は必須です。', 'error')
                return render_template('create_debate.html'), 400

        new_debate = Debate(
            title=params['title'],
            description=params['description'],
            method=params['method'],
            max_number_of_votes=params['max_number_of_votes'],
            max_turns=params['max_turns'],
            challenger_waiting_period_minutes=params['challenger_waiting_period_minutes'],
            debate_period_minutes=params['debate_period_minutes'],
            voting_period_minutes=params['voting_period_minutes'],
            turn_time_limit_minutes=params['turn_time_limit_minutes'],
            poster_id=poster_id,
        )

        # データベースに新しい議論を保存
        try:
            db.session.add(new_debate)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('議論の作成に失敗しました。', 'error')
            return render_template('create_debate.html'), 500

        flash('議論が作成されました。', 'info')
        return redirect(url_for('debate.get_debate', debate_id=new_debate.debate_id))
    else:
        return render_template('create_debate.html')

@bp.route('/debates/<int:debate_id>/edit', methods=['GET', 'POST'])
@login_required  # ログイン必須
def edit_debate(debate_id):
    """
    既存の議論を編集する
    GETリクエストで編集フォームを表示し、POSTリクエストで更新された情報を受け取り、データベースの議論を更新する

    Args:
        debate_id (int): 編集する議論のID

    Returns:
        GETリクエストの場合は議論編集フォームを含むHTMLページ
        POSTリクエストの場合は更新された議論の詳細ページにリダイレクト
    """
    poster_id = current_user.user_id  # ログインユーザーのIDを投稿者IDとして使用

    # データベースから議論を取得
    debate = Debate.query.get_or_404(debate_id)

    if request.method == 'POST':
        title = request.form.get('title', default=None, type=str)
        description = request.form.get('description', default=None, type=str)

        # バリデーション: タイトルと説明は必須
        title_len = len(title.strip()) if title else 0
        description_len = len(description.strip()) if description else 0

        if title_len == 0 or description_len == 0:
            flash('タイトルと説明は必須です。', 'error')
            return render_template('edit_debate.html', debate=debate), 400

        # データベースの議論を更新
        debate.title = title
        debate.description = description

        # 編集が許可されているかを確認
        # 例: 議論がすでに開始されている場合は編集を許可しない
        if debate.state != 0:  # stateが0（open）以外の場合は編集を許可しない
            db.session.rollback()  # 更新操作をロールバック
            flash('この議論はすでに開始されているため、編集できません。', 'error')
            return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 400
        elif debate.poster_id != poster_id:
            db.session.rollback()  # 更新操作をロールバック
            flash('この議論の投稿者のみが編集できます。', 'error')
            return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 403

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return render_template('edit_debate.html', debate=debate, error='議論の更新に失敗しました。'), 500

        flash('議論が更新されました。', 'info')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id))
    else:
        return render_template('edit_debate.html', debate=debate)

@bp.route('/debates/<int:debate_id>/delete', methods=['POST'])
@login_required  # ログイン必須
def delete_debate(debate_id):
    """
    既存の議論を削除する
    POSTリクエストで議論IDを受け取り、データベースから該当する議論を削除する

    Args:
        debate_id (int): 削除する議論のID

    Returns:
        削除された議論の一覧ページにリダイレクト
    """
    poster_id = current_user.user_id # ログインユーザーのIDを投稿者IDとして使用

    # データベースから議論を取得
    debate = Debate.query.get_or_404(debate_id)

    # 削除が許可されているかを確認
    # 例: 議論がすでに開始されている場合は削除を許可しない
    if debate.state != 0:  # stateが0（open）以外の場合は削除を許可しない
        db.session.rollback()  # 削除操作をロールバック
        flash('この議論はすでに開始されているため、削除できません。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 400
    elif debate.poster_id != poster_id:
        db.session.rollback()  # 削除操作をロールバック
        flash('この議論の投稿者のみが削除できます。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 403

    try:
        db.session.delete(debate)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('議論の削除に失敗しました。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 500

    flash('議論が削除されました。', 'info')
    return redirect(url_for('debate.get_debates'))

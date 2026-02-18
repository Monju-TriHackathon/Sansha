from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, request, render_template, url_for, redirect
from flaskr import db
from flaskr.models import Debate, Tag, DebateTag, Exchange, Notification
from flask_login import login_required, current_user

bp = Blueprint('debate', __name__)

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

    # 状態の更新チェック
    changed = False
    for debate in debates:
        if _update_debate_state(debate):
            changed = True
    if changed:
        db.session.commit()

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

    # 状態の更新チェック
    if _update_debate_state(debate):
        db.session.commit()

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
        error = _validate_debate_form(request.form)
        if error:
            flash(error, 'error')
            return render_template('create_debate.html'), 400

        # フォームデータから Debate オブジェクトを生成
        new_debate = _build_debate(request.form, poster_id)

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

    # 投稿者以外は編集不可
    if debate.poster_id != poster_id:
        flash('この議論の投稿者のみが編集できます。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 403

    if request.method == 'POST':
        title = request.form.get('title', default=None, type=str)
        description = request.form.get('description', default=None, type=str)

        # バリデーション: タイトルと説明は必須
        title_len = len(title.strip()) if title else 0
        description_len = len(description.strip()) if description else 0

        if title_len == 0 or description_len == 0:
            flash('タイトルと説明は必須です。', 'error')
            return render_template('edit_debate.html', debate=debate), 400

        # 議論がすでに開始されている場合は編集を許可しない
        if debate.state != 0:  # state 0: open, 1: in_debate, 2: voting, 3: closed
            flash('この議論はすでに開始されているため、編集できません。', 'error')
            return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 400

        # データベースの議論を更新
        debate.title = title
        debate.description = description

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
    if debate.poster_id != poster_id: # 投稿者以外は削除不可
        flash('この議論の投稿者のみが削除できます。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 403

    if debate.state != 0:  # stateが0（open）以外の場合は削除を許可しない
        flash('この議論はすでに開始されているため、削除できません。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 400

    try:
        db.session.delete(debate)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('議論の削除に失敗しました。', 'error')
        return redirect(url_for('debate.get_debate', debate_id=debate.debate_id)), 500

    flash('議論が削除されました。', 'info')
    return redirect(url_for('debate.get_debates'))

@bp.route('/debates/<int:debate_id>/post', methods=['POST'])
@login_required
def post_opinion(debate_id):
    """
    議論に意見を投稿する (JSON API)

    Args:
        debate_id (int): 意見を投稿する議論のID

    Request Body (JSON):
        message (str): 投稿する意見の内容

    Returns:
        JSON レスポンス
    """
    MAX_MESSAGE_LENGTH = 2000

    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()

    # --- バリデーション ---
    if len(message) == 0:
        return jsonify({'status': 'error', 'message': '意見の内容は必須です。'}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({'status': 'error', 'message': f'意見は{MAX_MESSAGE_LENGTH}文字以内で入力してください。'}), 400

    sender_id = current_user.user_id
    now = datetime.now(timezone.utc)

    try:
        # --- 議論の取得 ---
        debate = db.session.get(Debate, debate_id)
        if debate is None:
            return jsonify({'status': 'error', 'message': '議論が見つかりません。'}), 404

        # --- 状態チェック: in_debate(1) であること ---
        if debate.state != 1:
            return jsonify({'status': 'error', 'message': 'この議論は現在意見の投稿を受け付けていません。'}), 409

        # --- 参加者チェック (共通) ---
        if sender_id != debate.poster_id and sender_id != debate.challenger_id:
            return jsonify({'status': 'error', 'message': 'この議論の参加者ではないため、意見を投稿できません。'}), 403

        # --- 議論期間チェック ---
        if debate.debate_start_time is not None:
            elapsed_minutes = (now - _ensure_aware(debate.debate_start_time)).total_seconds() / 60
            if elapsed_minutes > debate.debate_period_minutes:
                debate.state = 2  # voting
                debate.voting_start_time = now
                _notify_both(debate, '議論期間が終了しました。投票期間に移行します。')
                db.session.commit()
                return jsonify({'status': 'error', 'message': '議論期間が終了しました。'}), 409

        # --- ターン制固有の処理 ---
        if debate.method == 0:
            # 発言者チェック: current_speaker(0=poster, 1=challenger)
            if debate.current_speaker == 0 and sender_id != debate.poster_id:
                return jsonify({'status': 'error', 'message': '現在はあなたの発言順番ではありません。'}), 403
            if debate.current_speaker == 1 and sender_id != debate.challenger_id:
                return jsonify({'status': 'error', 'message': '現在はあなたの発言順番ではありません。'}), 403

            # ターン時間制限チェック
            if debate.current_speaker_started_at is not None and debate.turn_time_limit_minutes is not None:
                turn_elapsed = (now - _ensure_aware(debate.current_speaker_started_at)).total_seconds() / 60
                if turn_elapsed > debate.turn_time_limit_minutes:
                    debate.state = 3  # closed
                    debate.finish_reason = 2  # time_out
                    # タイムアウトした側が負け
                    if debate.current_speaker == 0:
                        debate.outcome = 1  # challenger_win
                    else:
                        debate.outcome = 0  # poster_win
                    _notify_both(debate, '発言時間制限を超過したため、議論が終了しました。')
                    db.session.commit()
                    return jsonify({'status': 'error', 'message': '発言時間制限を超過しています。'}), 409

        # --- 意見の保存 ---
        exchange = Exchange(
            debate_id=debate_id,
            sender_id=sender_id,
            message=message,
            turn_number=debate.current_turn if debate.method == 0 else None,
        )
        db.session.add(exchange)

        # --- ターン更新 (ターン制のみ) ---
        if debate.method == 0:
            if debate.current_speaker == 1:  # Challenger が投稿した場合
                debate.current_turn = (debate.current_turn or 1) + 1
                debate.current_speaker = 0  # 次は Poster
                debate.current_speaker_started_at = now

                # 終了条件: ターン数が max_turns を超えた場合 → voting へ
                if debate.max_turns is not None and debate.current_turn > debate.max_turns:
                    debate.state = 2  # voting
                    debate.voting_start_time = now
                    _notify_both(debate, '最大ターン数に達しました。投票期間に移行します。')
            else:  # Poster が投稿した場合
                debate.current_speaker = 1  # 次は Challenger
                debate.current_speaker_started_at = now

        # --- 通知保存 (相手に通知) ---
        opponent_id = debate.challenger_id if sender_id == debate.poster_id else debate.poster_id
        if opponent_id is not None:
            notification = Notification(
                user_id=opponent_id,
                message=f'議論「{debate.title}」に新しい意見が投稿されました。',
            )
            db.session.add(notification)

        db.session.commit()

        return jsonify({'status': 'success', 'message': '意見を投稿しました。'}), 201

    except Exception:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '意見の投稿に失敗しました。'}), 500

def _validate_debate_form(form):
    """議論作成フォームのバリデーション。エラーメッセージを返す。問題なければ None。"""
    title = form.get('title', '', type=str)
    description = form.get('description', '', type=str)
    method = form.get('method', 0, type=int)

    if len(title.strip()) == 0 or len(description.strip()) == 0:
        return 'タイトルと説明は必須です。'

    if method == 0:
        max_turns = form.get('max_turns', type=int)
        turn_time_limit = form.get('turn_time_limit_minutes', type=int)
        if max_turns is None or turn_time_limit is None:
            return 'ターン制議論の場合、最大ターン数とターン時間制限は必須です。'

    return None

def _build_debate(form, poster_id):
    """フォームデータから Debate オブジェクトを生成する"""
    debate = Debate(
        title=form.get('title', type=str),
        description=form.get('description', type=str),
        poster_id=poster_id,
    )

    # フォームに値がある場合のみ上書き（なければモデルのデフォルト値が使われる）
    optional_int_fields = [
        'method', 'max_number_of_votes', 'max_turns',
        'challenger_waiting_period_minutes', 'debate_period_minutes',
        'voting_period_minutes', 'turn_time_limit_minutes',
    ]
    for field in optional_int_fields:
        value = form.get(field, type=int)
        if value is not None:
            setattr(debate, field, value)

    # ターン制の場合は初期状態をセット
    if debate.method == 0:
        debate.current_speaker = 1 # Challenger が最初の発言者
        debate.current_turn = 1

    return debate

def _ensure_aware(dt):
    """timezone-naive な datetime を UTC として扱う"""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def _notify_both(debate, message):
    """議論の両参加者に通知を保存するヘルパー"""
    for user_id in [debate.poster_id, debate.challenger_id]:
        if user_id is not None:
            notification = Notification(
                user_id=user_id,
                message=message,
            )
            db.session.add(notification)

def _update_debate_state(debate):
    """議論の状態を時間経過に基づいて更新する。変更があれば True を返す。"""
    now = datetime.now(timezone.utc)
    changed = False

    # open: 挑戦者待機期間を超過 -> closed (no_show, draw)
    if debate.state == 0:
        created = _ensure_aware(debate.created_at)
        elapsed = (now - created).total_seconds() / 60
        if elapsed > debate.challenger_waiting_period_minutes:
            debate.state = 3
            debate.outcome = 2  # draw
            debate.finish_reason = 1  # no_show
            _notify_both(debate, '挑戦者待機期間を超過したため、議論が終了しました。')
            changed = True

    # in_debate
    elif debate.state == 1:
        # 議論期間を超過 -> voting
        if debate.debate_start_time is not None:
            elapsed = (now - _ensure_aware(debate.debate_start_time)).total_seconds() / 60
            if elapsed > debate.debate_period_minutes:
                debate.state = 2  # voting
                debate.voting_start_time = now
                _notify_both(debate, '議論期間が終了しました。投票期間に移行します。')
                changed = True

        # ターン制: 発言時間制限を超過 -> closed (time_out)
        if debate.state == 1 and debate.method == 0:
            if debate.current_speaker_started_at is not None and debate.turn_time_limit_minutes is not None:
                turn_elapsed = (now - _ensure_aware(debate.current_speaker_started_at)).total_seconds() / 60
                if turn_elapsed > debate.turn_time_limit_minutes:
                    debate.state = 3  # closed
                    debate.finish_reason = 2  # time_out
                    if debate.current_speaker == 0:
                        debate.outcome = 1  # challenger_win
                    else:
                        debate.outcome = 0  # poster_win
                    _notify_both(debate, '発言時間制限を超過したため、議論が終了しました。')
                    changed = True

    # voting: 投票期間を超過 -> closed (normal, 勝敗判定)
    elif debate.state == 2:
        if debate.voting_start_time is not None:
            elapsed = (now - _ensure_aware(debate.voting_start_time)).total_seconds() / 60
            if elapsed > debate.voting_period_minutes:
                debate.state = 3  # closed
                debate.finish_reason = 0  # normal
                debate.outcome = _judge_outcome(debate)
                _notify_both(debate, '投票期間が終了しました。議論が終了しました。')
                changed = True

    return changed


def _judge_outcome(debate):
    """投票結果から勝敗を判定する。poster_win(0)/challenger_win(1)/draw(2)"""
    poster_votes = sum(1 for v in debate.votes if v.voting_destination == 0)
    challenger_votes = sum(1 for v in debate.votes if v.voting_destination == 1)
    if poster_votes > challenger_votes:
        return 0
    elif challenger_votes > poster_votes:
        return 1
    else:
        return 2

@bp.route('/debates/<int:debate_id>/exchanges', methods=['GET'])
def get_exchanges(debate_id):
    """
    議論のやり取り一覧をJSON形式で返す (ポーリング用API)

    Args:
        debate_id (int): 議論のID

    Returns:
        JSON レスポンス (exchanges のリスト, 議論の状態)
    """
    debate = db.session.get(Debate, debate_id)
    if debate is None:
        return jsonify({'status': 'error', 'message': '議論が見つかりません。'}), 404

    # 状態の更新チェック
    if _update_debate_state(debate):
        db.session.commit()

    exchanges = Exchange.query.filter_by(debate_id=debate_id).order_by(Exchange.sent_at.asc()).all()

    return jsonify({
        'status': 'success',
        'state': debate.state,
        'poster_id': debate.poster_id,
        'method': debate.method,
        'current_turn': debate.current_turn,
        'max_turns': debate.max_turns,
        'exchanges': [
            {
                'exchange_id': e.exchange_id,
                'sender': e.sender.username,
                'sender_id': e.sender_id,
                'message': e.message,
                'sent_at': e.sent_at.isoformat() if e.sent_at else None,
                'turn_number': e.turn_number,
            }
            for e in exchanges
        ],
    })

"""
投票・コメント機能のルーティングとロジック
"""
from datetime import datetime, timezone
from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from flaskr import db
from flaskr.models.debate import Debate
from flaskr.models.vote import Vote
from flaskr.models.comment import Comment
from flaskr.models.notification import Notification

bp = Blueprint('vote', __name__)


@bp.route('/debates/<int:debate_id>/vote', methods=['GET'])
@login_required
def vote_form(debate_id):   # 投票フォームを表示する

    debate = Debate.query.get_or_404(debate_id)

    # 議論の状態が voting(2) でない場合はフォームを無効化
    if debate.state != 2:
        flash('この議論は現在投票を受け付けていません。', 'error')

    return render_template('vote.html', debate=debate)


@bp.route('/debates/<int:debate_id>/vote', methods=['POST'])
@login_required
def submit_vote(debate_id):   # 投票とコメントを送信する
    
    voter_id = current_user.user_id

    # フォームからデータを取得
    voting_destination = request.form.get('voting_destination', type=int)
    comment_text = request.form.get('comment', '').strip()

    # コメントのバリデーション
    if not comment_text:
        flash('コメントは必須です。', 'error')
        return redirect(url_for('vote.vote_form', debate_id=debate_id))

    # 投票先のバリデーション
    if voting_destination not in (0, 1):
        flash('投票先を選択してください。', 'error')
        return redirect(url_for('vote.vote_form', debate_id=debate_id))

    try:
        now = datetime.now(timezone.utc)

        # トランザクション開始（悲観ロック付きで議論を取得）
        debate = db.session.query(Debate).with_for_update().filter_by(
            debate_id=debate_id
        ).first()

        if not debate:
            db.session.rollback()
            flash('指定された議論が見つかりません。', 'error')
            return redirect(url_for('vote.vote_form', debate_id=debate_id))

        # 議論状態の確認（voting(2) であること）
        if debate.state != 2:
            db.session.rollback()
            flash('この議論は現在投票を受け付けていません。', 'error')
            return redirect(url_for('vote.vote_form', debate_id=debate_id))

        # 投票期間の確認
        if debate.voting_start_time and debate.voting_period_minutes:
            voting_start_utc = debate.voting_start_time.replace(tzinfo=timezone.utc) if debate.voting_start_time.tzinfo is None else debate.voting_start_time
            elapsed_minutes = (now - voting_start_utc).total_seconds() / 60
            if elapsed_minutes > debate.voting_period_minutes:
                # 投票期間を超過 — 議論をクローズして勝敗を判定
                _close_debate_and_judge(debate, now)

                # Poster と Challenger への通知を保存
                _save_close_notifications(debate, now)
                db.session.commit()

                flash('投票期間が終了しています。', 'error')
                return redirect(url_for('vote.vote_form', debate_id=debate_id))

        # 自分の議論には投票できない
        if debate.poster_id == voter_id or debate.challenger_id == voter_id:
            db.session.rollback()
            flash('自分が参加している議論には投票できません。', 'error')
            return redirect(url_for('vote.vote_form', debate_id=debate_id))

        # 重複投票チェック
        existing_vote = Vote.query.filter_by(
            debate_id=debate_id, voter_id=voter_id
        ).first()
        if existing_vote:
            db.session.rollback()
            flash('この議論にはすでに投票済みです。', 'error')
            return redirect(url_for('vote.vote_form', debate_id=debate_id))

        # 投票の保存
        new_vote = Vote(
            debate_id=debate_id,
            voter_id=voter_id,
            voting_destination=voting_destination,
            voted_at=now,
        )
        db.session.add(new_vote)
        db.session.flush()

        # コメントの保存
        new_comment = Comment(
            debate_id=debate_id,
            poster_id=voter_id,
            comment=comment_text,
            posted_at=now,
        )
        db.session.add(new_comment)
        db.session.flush()

        # 投票数の更新
        debate.current_number_of_votes += 1
        debate.updated_at = now

        # 投票終了条件の確認
        if debate.current_number_of_votes >= debate.max_number_of_votes:
            # 最大投票数に達した場合 — 議論をクローズして勝敗を判定
            _close_debate_and_judge(debate, now)

            # Poster と Challenger への通知を保存
            _save_close_notifications(debate, now)
        else:
            # 成功通知 — 相手（poster/challenger）への通知を保存
            _save_vote_notification(debate, voter_id, now)

        # トランザクションのコミット
        db.session.commit()

        if debate.state == 3:
            flash('投票とコメントを送信しました。この投票で議論が終了しました。', 'success')
        else:
            flash('投票とコメントを送信しました。', 'success')
        return redirect(url_for('vote.vote_form', debate_id=debate_id))

    except Exception:
        db.session.rollback()
        flash('予期しないエラーが発生しました。', 'error')
        return redirect(url_for('vote.vote_form', debate_id=debate_id))


def _judge_outcome(debate):    # 投票結果から勝敗を判定する
    poster_votes = Vote.query.filter_by(
        debate_id=debate.debate_id, voting_destination=0
    ).count()
    challenger_votes = Vote.query.filter_by(
        debate_id=debate.debate_id, voting_destination=1
    ).count()

    if poster_votes > challenger_votes:
        return 0  # poster_win
    elif challenger_votes > poster_votes:
        return 1  # challenger_win
    else:
        return 2  # draw


def _close_debate_and_judge(debate, now):    # 議論をクローズし、勝敗を判定して保存する
    debate.state = 3  # closed
    debate.outcome = _judge_outcome(debate)
    debate.finish_reason = 0  # normal
    debate.updated_at = now


def _save_close_notifications(debate, now):    # 議論クローズ時に Poster と Challenger に通知を保存する

    outcome_text = {0: '投稿者の勝利', 1: '挑戦者の勝利', 2: '引き分け'}
    result_message = outcome_text.get(debate.outcome, '不明')

    for user_id in [debate.poster_id, debate.challenger_id]:
        if user_id is not None:
            notification = Notification(
                user_id=user_id,
                message=f'「{debate.title}」の投票が終了しました。結果: {result_message}',
                is_read=False,
                created_at=now,
            )
            db.session.add(notification)
    db.session.flush()


def _save_vote_notification(debate, voter_id, now):    # 投票成功時に議論の参加者（poster/challenger）へ通知を保存する

    # poster と challenger の両方に通知
    for user_id in [debate.poster_id, debate.challenger_id]:
        if user_id is not None and user_id != voter_id:
            notification = Notification(
                user_id=user_id,
                message=f'「{debate.title}」に新しい投票がありました。',
                is_read=False,
                created_at=now,
            )
            db.session.add(notification)
    db.session.flush()

"""
挑戦状への参加機能のサービスロジック
"""
from datetime import datetime, timezone
from flaskr import db
from flaskr.models.user import User
from flaskr.models.debate import Debate
from flaskr.models.notification import Notification


class JoinChallengeError(Exception):
    """挑戦状参加時のエラー"""
    pass



from flask import Blueprint, request, jsonify

bp = Blueprint('join_challenge', __name__, url_prefix='/debates')

@bp.route('/create', methods=['POST'])
def create_debate_route():
    try:
        data = request.get_json()
        result = create_debate(
            poster_id=data.get('poster_id'),
            title=data.get('title'),
            description=data.get('description'),
            method=data.get('method', 0),
            max_number_of_votes=data.get('max_number_of_votes'),
            challenger_waiting_period_minutes=data.get('challenger_waiting_period_minutes'),
            debate_period_minutes=data.get('debate_period_minutes'),
            voting_period_minutes=data.get('voting_period_minutes'),
            max_turns=data.get('max_turns'),
            turn_time_limit_minutes=data.get('turn_time_limit_minutes')
        )
        return jsonify(result), 201
    except JoinChallengeError as e:
        return jsonify({"successful": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"successful": False, "message": f"エラー: {str(e)}"}), 500

@bp.route('/<int:debate_id>/join', methods=['POST'])
def join_debate_route(debate_id):
    try:
        data = request.get_json()
        challenger_id = data.get('challenger_id')
        
        result = join_challenge(debate_id, challenger_id)
        return jsonify(result), 200
    except JoinChallengeError as e:
        return jsonify({"successful": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"successful": False, "message": f"エラー: {str(e)}"}), 500


def create_debate(poster_id: int, title: str, description: str, method: int, 
                 max_number_of_votes: int, challenger_waiting_period_minutes: int,
                 debate_period_minutes: int, voting_period_minutes: int,
                 max_turns: int = None, turn_time_limit_minutes: int = None) -> dict:
    """
    挑戦状を作成
    
    Args:
        poster_id: 投稿者ID
        title: 議題タイトル
        description: 議題説明
        method: 議論方法 (turn(0)/realtime(1))
        max_number_of_votes: 最大投票数
        challenger_waiting_period_minutes: 挑戦者待機時間（分）
        debate_period_minutes: 議論期間（分）
        voting_period_minutes: 投票期間（分）
        max_turns: 最大ターン数（method=0の場合）
        turn_time_limit_minutes: ターン時間制限（分、method=0の場合）
    
    Returns:
        dict: 作成結果
    """
    try:
        # ユーザーが存在するか確認
        poster = db.session.query(User).filter_by(user_id=poster_id).first()
        if not poster:
            raise JoinChallengeError("投稿者が見つかりません")
        
        # 新しい挑戦状を作成
        now = datetime.now(timezone.utc)
        debate = Debate(
            poster_id=poster_id,
            title=title,
            description=description,
            state=0,  # open
            method=method,
            max_number_of_votes=max_number_of_votes,
            challenger_waiting_period_minutes=challenger_waiting_period_minutes,
            debate_period_minutes=debate_period_minutes,
            voting_period_minutes=voting_period_minutes,
            max_turns=max_turns if method == 0 else None,
            turn_time_limit_minutes=turn_time_limit_minutes if method == 0 else None,
            created_at=now,
            updated_at=now
        )
        
        db.session.add(debate)
        db.session.commit()
        
        return {
            "successful": True,
            "debate_id": debate.debate_id,
            "message": "挑戦状を作成しました",
            "debate": {
                "debate_id": debate.debate_id,
                "title": debate.title,
                "state": debate.state,
                "poster_id": debate.poster_id
            }
        }
    
    except JoinChallengeError:
        raise
    except Exception as e:
        db.session.rollback()
        raise JoinChallengeError(f"挑戦状作成エラー: {str(e)}")


def join_challenge(debate_id: int, challenger_id: int) -> dict:
    
    try:
        # トランザクション開始（悲観ロック）
        debate = db.session.query(Debate).with_for_update().filter_by(
            debate_id=debate_id
        ).first()

        # 1. 挑戦状が存在するか確認
        if not debate:
            db.session.rollback()
            raise JoinChallengeError("指定された挑戦状が見つかりません")

        # 2. 挑戦状の状態を確認（open であること）
        if debate.state != 0:  # 0: open
            db.session.rollback()
            state_name = {0: "open", 1: "in_debate", 2: "voting", 3: "closed"}.get(debate.state, "unknown")
            raise JoinChallengeError(f"この挑戦状は参加できません（現在の状態: {state_name}）")

        # 3. 挑戦者がいないことを確認
        if debate.challenger_id is not None:
            db.session.rollback()
            raise JoinChallengeError("この挑戦状には既に挑戦者がいます")

        # 4. 投稿者と挑戦者が同じユーザーでないか確認
        if debate.poster_id == challenger_id:
            db.session.rollback()
            raise JoinChallengeError("自分の挑戦状には参加できません")

        # 5. ユーザーが存在するか確認
        challenger = db.session.query(User).filter_by(
            user_id=challenger_id
        ).first()
        if not challenger:
            db.session.rollback()
            raise JoinChallengeError("ユーザーが見つかりません")

        # 6. 参加登録（状態の更新と参加者の登録）
        now = datetime.now(timezone.utc)
        debate.challenger_id = challenger_id
        debate.state = 1  # in_debate
        debate.current_turn = 1
        debate.current_speaker = 1  # challenger
        debate.debate_start_time = now
        debate.current_speaker_started_at = now
        debate.updated_at = now

        db.session.add(debate)
        db.session.flush()

        # 7. 通知を保存（投稿者に対して）
        poster_notification = Notification()
        poster_notification.user_id = debate.poster_id
        poster_notification.message = f'"{debate.title}"への参加要求: {challenger.username}'
        poster_notification.is_read = False
        poster_notification.created_at = now
        db.session.add(poster_notification)
        db.session.flush()

        # 8. トランザクションコミット
        db.session.commit()

        return {
            "successful": True,
            "debate_id": debate.debate_id,
            "message": "参加成功しました",
            "debate": {
                "debate_id": debate.debate_id,
                "title": debate.title,
                "state": debate.state,
                "challenger_id": debate.challenger_id,
                "current_speaker": debate.current_speaker,
                "debate_start_time": debate.debate_start_time.isoformat()
            }
        }

    except JoinChallengeError:
        raise
    except Exception as e:
        db.session.rollback()
        raise JoinChallengeError(f"予期しないエラーが発生しました: {str(e)}")

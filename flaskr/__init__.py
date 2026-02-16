import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    """
    Flask アプリケーションを作成

    Returns:
        app: Flask アプリケーションのインスタンス
        db: SQLAlchemy データベースのインスタンス
    """
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///database.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # インスタンスフォルダが存在しない場合は作成
    os.makedirs(app.instance_path, exist_ok=True)

    # データベースの初期化
    db.init_app(app)

    # アプリケーションコンテキスト内でテーブルを作成
    with app.app_context():
        # ここでモデルをインポート（db初期化後）
        from . import models
        db.create_all()

    # アプリケーションのルートを定義
    from .models.join_challenge import join_challenge, JoinChallengeError, create_debate

    @app.route('/')
    def index():
        return render_template('base.html')

    @app.route('/debates/<int:debate_id>/join', methods=['POST'])
    def join_debate(debate_id):
        try:
            data = request.get_json()
            challenger_id = data.get('challenger_id')
            
            result = join_challenge(debate_id, challenger_id)
            return jsonify(result), 200
        except JoinChallengeError as e:
            return jsonify({"successful": False, "message": str(e)}), 400
        except Exception as e:
            return jsonify({"successful": False, "message": f"エラー: {str(e)}"}), 500

    @app.route('/debates/create', methods=['POST'])
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

    return app

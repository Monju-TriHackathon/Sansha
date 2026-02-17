import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'ログインが必要です'

def create_app(test_config=None):
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
        SECRET_KEY='dev',
    )

    # インスタンスフォルダが存在しない場合は作成
    os.makedirs(app.instance_path, exist_ok=True)

    # データベースの初期化
    db.init_app(app)

    # Flask-Loginの初期化
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from flaskr.models.user import User
        return User.query.get(int(user_id))

    # アプリケーションコンテキスト内でテーブルを作成
    with app.app_context():
        from flaskr import models # モデルをインポートしてテーブルを認識させる
        db.create_all()

        # ============================================================
        # ================== テスト用データ（ここから） ==================
        # ============================================================
        # ※ 動作確認が終わったらこのブロックごと削除してください
        # ※ 既にデータがある場合はスキップします
        from flaskr.models.user import User
        from flaskr.models.debate import Debate
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timezone

        if not User.query.first():
            # テストユーザー3名を作成
            user1 = User(
                username='poster_user',
                password=generate_password_hash('password'),
                mailaddress='poster@test.com',
            )
            user2 = User(
                username='challenger_user',
                password=generate_password_hash('password'),
                mailaddress='challenger@test.com',
            )
            user3 = User(
                username='voter_user',
                password=generate_password_hash('password'),
                mailaddress='voter@test.com',
            )
            db.session.add_all([user1, user2, user3])
            db.session.flush()

            # 投票受付中(state=2)のテスト議論を作成
            test_debate = Debate(
                poster_id=user1.user_id,
                challenger_id=user2.user_id,
                title='テスト議論: 猫 vs 犬',
                description='猫と犬、どちらが最高のペットか？',
                state=2,  # voting
                method=0,
                max_number_of_votes=10,
                max_turns=5,
                challenger_waiting_period_minutes=120,
                debate_period_minutes=1440,
                voting_period_minutes=1440,
                turn_time_limit_minutes=30,
                voting_start_time=datetime.now(timezone.utc),
            )
            db.session.add(test_debate)
            db.session.commit()
            print('=== テストデータを作成しました ===')
        # ============================================================
        # ================== テスト用データ（ここまで） ==================
        # ============================================================

    # アプリケーションのルートを定義
    from flaskr import main, debate, vote

    app.register_blueprint(main.bp)
    app.register_blueprint(debate.bp)
    app.register_blueprint(vote.bp)

    from flaskr import auth
    app.register_blueprint(auth.bp)

    return app

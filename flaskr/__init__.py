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

    # アプリケーションのルートを定義
    from flaskr import main, debate

    app.register_blueprint(main.bp)
    app.register_blueprint(debate.bp)

    from flaskr import auth
    app.register_blueprint(auth.bp)

    from flaskr import notification
    app.register_blueprint(notification.bp)

    return app

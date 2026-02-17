import os
from flask import Flask
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
        SECRET_KEY='dev',  #セッション機能の使用
    )

    # インスタンスフォルダが存在しない場合は作成
    os.makedirs(app.instance_path, exist_ok=True)

    # データベースの初期化
    db.init_app(app)

    # アプリケーションコンテキスト内でテーブルを作成
    with app.app_context():
        db.create_all()

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .join_challenge import bp as join_challenge_bp
    app.register_blueprint(join_challenge_bp)

    return app

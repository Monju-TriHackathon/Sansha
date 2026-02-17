import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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

    # アプリケーションコンテキスト内でテーブルを作成
    with app.app_context():
        from flaskr import models # モデルをインポートしてテーブルを認識させる
        db.create_all()

    # アプリケーションのルートを定義
    from flaskr import main, debate

    app.register_blueprint(main.bp)
    app.register_blueprint(debate.bp)

    return app

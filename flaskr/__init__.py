import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from . import main

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

    # アプリケーションのルートを定義
    app.register_blueprint(main.bp)

    return app

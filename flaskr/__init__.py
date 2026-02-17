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
    from .join_challenge import bp as join_challenge_bp
    app.register_blueprint(join_challenge_bp)

    @app.route('/')
    def index():
        return render_template('base.html')

    return app

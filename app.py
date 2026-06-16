import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.INFO)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, redirect, url_for
from config import Config
from database.db import mysql


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    mysql.init_app(app)

    from routes.auth_routes import auth_bp
    from routes.mfa_routes import mfa_bp 
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(mfa_bp)
    app.register_blueprint(dashboard_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()


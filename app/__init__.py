# -*- coding: utf-8 -*-
import pendulum
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import RedisSessionInterface
from celery import Celery
from redis import StrictRedis
from config import config, Config

db = SQLAlchemy()
sr = StrictRedis()
mail = Mail()
migrate = Migrate()

celery_app = Celery(__name__)
celery_app.config_from_object(Config, namespace='CELERY')

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def timesince(dt):
    return pendulum.instance(dt).diff_for_humans()


def create_app(config_name):
    app = Flask(__name__)
    app.jinja_env.auto_reload = True  # 静态资源修改不更新问题
    app.jinja_env.filters['timesince'] = timesince
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    app.session_interface = RedisSessionInterface(
        sr,
        app.config['SESSION_KEY_PREFIX']
    )

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app

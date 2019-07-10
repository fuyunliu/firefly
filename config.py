# -*- coding: utf-8 -*-

import os

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:

    # session and cookie
    SERVER_NAME = '127.0.0.1:5000'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SESSION_KEY_PREFIX = 'session:'

    # email
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'fuyunliux@163.com'
    MAIL_PASSWORD = 'zaq1xsw2'
    MAIL_SENDER = 'Firefly Admin <fuyunliux@163.com>'
    MAIL_SUBJECT_PREFIX = '[Firefly]'
    MAIL_ADMIN = 'fuyunliux@163.com'

    # database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # celery
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_ACCEPT_CONTENT = ['pickle', 'json']

    # common settings
    PER_PAGE_SIZE = 10
    DEFAULT_USER_AVATAR = ("https://wx4.sinaimg.cn/orj360/"
                           "0066oo9Jly1g4uykx25gqj301e01e3ye.jpg")

    @staticmethod
    def init_app(app):
        pass


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://fuyun:fuyun@localhost:5432/firefly'


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'test.db')
    WTF_CSRF_ENABLED = False


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
    'default': DevConfig
}

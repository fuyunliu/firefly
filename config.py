# -*- coding: utf-8 -*-

import os

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'fuyunliux@163.com'
    MAIL_PASSWORD = 'zaq1xsw2'
    MAIL_SENDER = 'Firefly Admin <fuyunliux@163.com>'
    MAIL_SUBJECT_PREFIX = '[Firefly]'
    FIREFLY_ADMIN = 'fuyunliux@163.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

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
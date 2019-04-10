# -*- coding: utf-8 -*-
import sys
sys.path.append('..')
import unittest
from flask import current_app
from flask_mail import Message
from app import create_app, db, mail


class BasicsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

    def test_send_mail(self):
        sender = 'Firefly Admin <firefly@163.com>'
        msg = Message('hello', sender=sender, recipients=['920507252@qq.com'])
        mail.send(msg)


if __name__ == "__main__":
    unittest.main()

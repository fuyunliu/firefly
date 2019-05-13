# -*- coding: utf-8 -*-
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post


def users(count=100):
    fake = Faker()
    while count > 0:
        user = User(
            email=fake.email(),
            username=fake.user_name(),
            password='password',
            confirmed=True,
            name=fake.name(),
            location=fake.city(),
            about_me=fake.text(),
            member_since=fake.past_date()
        )
        db.session.add(user)
        try:
            db.session.commit()
            count -= 1
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker()
    user_count = User.query.count()
    for _ in range(count):
        user = User.query.offset(randint(0, user_count - 1)).first()
        post = Post(
            body=fake.text(),
            timestamp=fake.past_date(),
            author=user
        )
        db.session.add(post)
    db.session.commit()

# -*- coding: utf-8 -*-
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker

from app import db, create_app
from app.models import User, Post, Comment


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
            title=fake.sentence(),
            body=fake.text(),
            create_time=fake.past_date(),
            update_time=fake.past_date(),
            author=user
        )
        db.session.add(post)
    db.session.commit()


def comments(count=100):
    fake = Faker()
    user_count = User.query.count()
    for post in Post.query.all():
        for _ in range(count):
            user = User.query.offset(randint(0, user_count - 1)).first()
            comment = Comment(
                body=fake.sentence(),
                post=post,
                author=user
            )
            db.session.add(comment)
    db.session.commit()


def run():
    app = create_app('default')
    with app.app_context():
        # users(100)
        # posts(100)
        comments(100)


if __name__ == "__main__":
    run()

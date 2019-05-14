# -*- coding: utf-8 -*-

import hashlib
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return f'<Role {self.name}>'


class Follow(db.Model):
    __tablename__ = 'me_follow_you'
    me_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    you_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    create_time = db.Column(db.DateTime(), default=datetime.utcnow)


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reply_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    like_count = db.Column(db.Integer)
    create_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

    def dump(self):
        pass

    @staticmethod
    def load():
        pass


class UserLikePost(db.Model):
    __tablename__ = 'user_like_post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    create_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)


class UserLikeComment(db.Model):
    __tablename__ = 'user_like_comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    create_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    passwd_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # 我关注的人
    stars = db.relationship('User',
                            secondary='me_follow_you',
                            primaryjoin=id==Follow.me_id,
                            lazy='dynamic')

    # 我的粉丝
    fans = db.relationship('User',
                           secondary='me_follow_you',
                           primaryjoin=id==Follow.you_id,
                           lazy='dynamic')

    # 我的文章
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # 我的评论
    comments = db.relationship('Comment',
                               foreign_keys=[Comment.author_id],
                               backref=db.backref('author', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    # 我收到的回复
    replies = db.relationship('Comment',
                              foreign_keys=[Comment.reply_id],
                              backref=db.backref('reply', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FIREFLY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        self.follow(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passwd_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passwd_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False

        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}
        ).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = "https://secure.gravatar.com/avatar"
        hash = self.avatar_hash or self.gravatar_hash()
        return f'{url}/{hash}?s={size}&d={default}&r={rating}'

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(me_id=self.id, you_id=user.id)
            db.session.add(f)

    def unfollow(self, user):
        f = Follow.filter_by(me_id=self.id, you_id=user.id).first()
        if f is not None:
            db.session.delete(f)

    def is_following(self, user):
        f = Follow.filter_by(me_id=self.id, you_id=user.id).first()
        return f is not None

    def is_followed_by(self, user):
        f = Follow.filter_by(me_id=user.id, you_id=self.id).first()
        return f is not None

    @property
    def followed_posts(self):
        return Post.query.join(
            Follow, Follow.you_id == Post.author_id
        ).filter(Follow.me_id == self.id)

    def like_post(self, post):
        pass

    def dislike_post(self, post):
        pass

    def is_like_post(self, post):
        if post.id is None:
            return False


    @property
    def liked_posts(self):
        pass

    def like_comment(self, comment):
        pass

    def dislike_comment(self, comment):
        pass

    @property
    def liked_comments(self):
        pass

    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return None
        return User.query.get(data.get('id'))

    def dump(self):
        user = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
        }
        return user

    def __repr__(self):
        return f'<User {self.username}>'


class AnonymousUser(AnonymousUserMixin):

    def can(self, perm):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    like_count = db.Column(db.Integer)
    create_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    update_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def on_change_body():
        pass

    def dump(self):
        pass

    @staticmethod
    def load():
        pass


db.event.listen(Post.body, 'set', Post.on_change_body)

# -*- coding: utf-8 -*-

import hashlib
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, url_for, g
from flask_login import UserMixin, AnonymousUserMixin, current_user
from . import db, login_manager, timesince


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
    me = db.relationship('User', foreign_keys=[me_id])
    you_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    you = db.relationship('User', foreign_keys=[you_id])
    create_time = db.Column(db.DateTime(), default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    passwd_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    token_create = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # stars=我关注的人 fans=我的粉丝
    stars = db.relationship('User',
                            secondary='me_follow_you',
                            primaryjoin='User.id==Follow.me_id',
                            secondaryjoin='User.id==Follow.you_id',
                            backref=db.backref('fans', lazy='dynamic'),
                            lazy='dynamic')

    # 我的文章
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # 我的评论
    comments = db.relationship('Comment',
                               foreign_keys='Comment.author_id',
                               backref=db.backref('author', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    # 我收到的回复
    replies = db.relationship('Comment',
                              foreign_keys='Comment.reply_id',
                              backref=db.backref('reply', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    # 我喜欢的文章
    liked_posts = db.relationship('Post',
                                  secondary='user_like_post',
                                  lazy='dynamic')

    # 我喜欢的评论
    liked_comments = db.relationship('Comment',
                                     secondary='user_like_comment',
                                     lazy='dynamic')

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
    def token_timestamp(self):
        return int(self.token_create.timestamp() * 1000)

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
        except Exception as e:
            print(e)
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
        except Exception as e:
            print(e)
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
        except Exception as e:
            print(e)
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
            f = Follow(me=self, you=user)
            db.session.add(f)

    def unfollow(self, user):
        f = Follow.query.filter_by(me_id=self.id, you_id=user.id).first()
        if f is not None:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        f = Follow.query.filter_by(me_id=self.id, you_id=user.id).first()
        return f is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        f = Follow.query.filter_by(me_id=user.id, you_id=self.id).first()
        return f is not None

    @property
    def followed_posts(self):
        return Post.query.join(
            Follow, Follow.you_id == Post.author_id
        ).filter(Follow.me_id == self.id)

    def like_post(self, post):
        if not self.is_like_post(post):
            lp = UserLikePost(user=self, post=post)
            post.like_count += 1
            db.session.add(lp)
            db.session.add(post)

    def dislike_post(self, post):
        lp = UserLikePost.query.filter_by(user_id=self.id,
                                          post_id=post.id).first()
        if lp is not None:
            post.like_count -= 1
            db.session.delete(lp)
            db.session.add(post)

    def is_like_post(self, post):
        if post.id is None:
            return False
        lp = UserLikePost.query.filter_by(user_id=self.id,
                                          post_id=post.id).first()
        return lp is not None

    def is_collect_post(self, post):
        return True

    def like_comment(self, comment):
        if not self.is_like_comment(comment):
            lc = UserLikeComment(user=self, comment=comment)
            comment.like_count += 1
            db.session.add(lc)
            db.session.add(comment)

    def dislike_comment(self, comment):
        lc = UserLikeComment.query.filter_by(user_id=self.id,
                                             comment_id=comment.id).first()
        if lc is not None:
            comment.like_count -= 1
            db.session.delete(lc)
            db.session.add(comment)

    def is_like_comment(self, comment):
        if comment.id is None:
            return False
        lc = UserLikeComment.query.filter_by(user_id=self.id,
                                             comment_id=comment.id).first()
        return lc is not None

    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        self.token_create = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
        return s.dumps({
            'id': self.id,
            'timestamp': self.token_timestamp
        }).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
            user = User.query.get(data.get('id'))
            assert data.get('timestamp') == user.token_timestamp
            return user
        except Exception as e:
            print(e)
            return None

    def dumps(self):
        user = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'member_since': self.member_since.year,
            'last_seen': timesince(self.last_seen),
            'url': url_for('api.user_api', user_id=self.id, _external=True)
        }
        return user

    @staticmethod
    def loads(data):
        return User(
            email=data['email'],
            username=data['username'],
            password=data['password']
        )

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


def get_current_user():
    user = getattr(g, 'current_user', None) or current_user
    if isinstance(user, AnonymousUser):
        return None
    return user


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author_name = db.Column(db.String(64))
    like_count = db.Column(db.Integer)
    create_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    update_time = db.Column(db.DateTime(),
                            default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    # 文章的评论
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    # 喜欢文章的人
    liked_users = db.relationship('User',
                                  secondary='user_like_post',
                                  lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.like_count is None:
            self.like_count = 0

    def dumps(self):
        data = {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'body_html': self.body_html,
            'create_time': timesince(self.create_time),
            'update_time': timesince(self.update_time),
            'author_id': self.author_id,
            'author_name': self.author_name,
            'like_count': self.like_count,
            'url': url_for('api.post_api', post_id=self.id, _external=True)
        }
        user = get_current_user()
        if user is not None:
            data['heart_css'] = 'heart'
            data['star_css'] = 'star'
            if user.is_like_post(self):
                data['heart_css'] = 'red heart'
            if user.is_collect_post(self):
                data['star_css'] = 'yellow star'
        return data

    @staticmethod
    def loads(data):
        return Post(
            title=data['title'],
            body=data['body']
        )

    def __repr__(self):
        return f'<Post {self.id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reply_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    like_count = db.Column(db.Integer)
    create_time = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

    # 喜欢评论的人
    liked_users = db.relationship('User',
                                  secondary='user_like_comment',
                                  lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.like_count is None:
            self.like_count = 0

    def __repr__(self):
        return f'<Comment {self.id}>'


class UserLikePost(db.Model):
    __tablename__ = 'user_like_post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    post = db.relationship('Post')
    create_time = db.Column(db.DateTime(), default=datetime.utcnow)


class UserLikeComment(db.Model):
    __tablename__ = 'user_like_comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    comment = db.relationship('Comment')
    create_time = db.Column(db.DateTime(), default=datetime.utcnow)

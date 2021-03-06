import hashlib
import urllib.parse as urlparse
from datetime import datetime
from functools import partial
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
    users = db.relationship('User',
                            backref=db.backref('role', lazy='joined'),
                            lazy='dynamic')

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
    created = db.Column(db.DateTime(), default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    passwd_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
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
    posts = db.relationship('Post',
                            backref=db.backref('author', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')

    # 我的推特
    tweets = db.relationship('Tweet',
                             backref=db.backref('author', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')

    # 我的评论
    comments = db.relationship('Comment',
                               foreign_keys='Comment.author_id',
                               backref=db.backref('author', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    # 我喜欢的文章
    liked_posts = db.relationship('Post',
                                  secondary='user_like_post',
                                  lazy='dynamic')

    # 我喜欢的推特
    liked_tweets = db.relationship('Tweet',
                                   secondary='user_like_tweet',
                                   lazy='dynamic')

    # 我喜欢的评论
    liked_comments = db.relationship('Comment',
                                     secondary='user_like_comment',
                                     lazy='dynamic')

    # 我收藏的文章
    collected_posts = db.relationship('Post',
                                      secondary='user_collect_post',
                                      lazy='dynamic')

    # 我的收藏夹
    favorites = db.relationship('Favorite',
                                backref=db.backref('user', lazy='joined'),
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
            if self.email == current_app.config['MAIL_ADMIN']:
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
        user = User.query.get(data['reset'])
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

    def gravatar(self, size=80):
        url = "https://gravatar.loli.net/avatar"
        hash = self.avatar_hash or self.gravatar_hash()
        query = {
            's': size,
            'd': 'mp',
            'r': 'g'
        }
        return f'{url}/{hash}?{urlparse.urlencode(query)}'

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
            db.session.add(lp)

    def dislike_post(self, post):
        lp = UserLikePost.query.filter_by(user_id=self.id,
                                          post_id=post.id).first()
        if lp is not None:
            db.session.delete(lp)

    def is_like_post(self, post):
        if post.id is None:
            return False
        lp = UserLikePost.query.filter_by(user_id=self.id,
                                          post_id=post.id).first()
        return lp is not None

    def collect_post(self, post):
        if not self.is_collect_post(post):
            cp = UserCollectPost(user=self, post=post)
            db.session.add(cp)

    def discollect_post(self, post):
        cp = UserCollectPost.query.filter_by(user_id=self.id,
                                             post_id=post.id).first()
        if cp is not None:
            db.session.delete(cp)

    def is_collect_post(self, post):
        if post.id is None:
            return False
        cp = UserCollectPost.query.filter_by(user_id=self.id,
                                             post_id=post.id).first()
        return cp is not None

    def like_tweet(self, tweet):
        if not self.is_like_tweet(tweet):
            lt = UserLikeTweet(user=self, tweet=tweet)
            db.session.add(lt)

    def dislike_tweet(self, tweet):
        lt = UserLikeTweet.query.filter_by(user_id=self.id,
                                           tweet_id=tweet.id).first()
        if lt is not None:
            db.session.delete(lt)

    def is_like_tweet(self, tweet):
        if tweet.id is None:
            return False
        lt = UserLikeTweet.query.filter_by(user_id=self.id,
                                           tweet_id=tweet.id).first()
        return lt is not None

    def collect_tweet(self, tweet):
        if not self.is_collect_tweet(tweet):
            ct = UserCollectTweet(user=self, tweet=tweet)
            db.session.add(ct)

    def discollect_tweet(self, tweet):
        ct = UserCollectTweet.query.filter_by(user_id=self.id,
                                              tweet_id=tweet.id).first()
        if ct is not None:
            db.session.delete(ct)

    def is_collect_tweet(self, tweet):
        if tweet.id is None:
            return False
        ct = UserCollectTweet.query.filter_by(user_id=self.id,
                                              tweet_id=tweet.id).first()
        return ct is not None

    def like_comment(self, comment):
        if not self.is_like_comment(comment):
            lc = UserLikeComment(user=self, comment=comment)
            db.session.add(lc)

    def dislike_comment(self, comment):
        lc = UserLikeComment.query.filter_by(user_id=self.id,
                                             comment_id=comment.id).first()
        if lc is not None:
            db.session.delete(lc)

    def is_like_comment(self, comment):
        if comment.id is None:
            return False
        lc = UserLikeComment.query.filter_by(user_id=self.id,
                                             comment_id=comment.id).first()
        return lc is not None

    def generate_auth_token(self, expiration=3600, token_type='access'):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'id': self.id, 'type': token_type}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            return s.loads(token.encode('utf-8'))
        except Exception as e:
            print(e)
            return None

    def dumps(self):
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'avatar': self.gravatar(size=18),
            'member_since': self.member_since.year,
            'last_seen': timesince(self.last_seen),
            'url': url_for('api.users', user_id=self.id, _external=True),
            'bio': url_for('auth.user', username=self.username, _external=True),
        }
        user = get_current_user()
        if user is not None:
            data['is_followed'] = self.is_followed_by(user)
            data['is_following'] = self.is_following(user)
        return data

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

    def ping(self):
        pass

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
    abstract = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 文章的评论
    comments = db.relationship('Comment',
                               backref=db.backref('post', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    # 喜欢文章的人
    liked_users = db.relationship('User',
                                  secondary='user_like_post',
                                  lazy='dynamic')

    # 收藏文章的人
    collected_users = db.relationship('User',
                                      secondary='user_collect_post',
                                      lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        truncate = partial(
            current_app.jinja_env.filters['truncate'],
            current_app.jinja_env)
        target.abstract = truncate(value, length=200)

    @property
    def like_count(self):
        return self.liked_users.count_all()

    @property
    def collect_count(self):
        return self.collected_users.count_all()

    @property
    def comment_count(self):
        return self.comments.count_all()

    def dumps(self):
        data = {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'body_html': self.body_html,
            'created': timesince(self.created),
            'updated': timesince(self.updated),
            'like_count': self.like_count,
            'collect_count': self.collect_count,
            'comment_count': self.comment_count,
            'url': url_for('api.posts', post_id=self.id, _external=True),
            'author': self.author.dumps()
        }
        user = get_current_user()
        if user is not None:
            data['is_liked'] = user.is_like_post(self)
            data['is_collected'] = user.is_collect_post(self)
        return data

    @staticmethod
    def loads(data):
        title = data.get('title')
        body = data.get('body')
        body_html = data.get('body_html')
        if (title is None or title.strip() == '') and \
                (body is None or body.strip() == ''):
            raise ValueError('post does not have a title or body')
        return Post(title=title, body=body, body_html=body_html)

    def __repr__(self):
        return f'<Post {self.id}>'


class Tweet(db.Model):
    __tablename__ = 'tweets'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    abstract = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created = db.Column(db.DateTime(), index=True, default=datetime.utcnow)

    # 推特的评论
    comments = db.relationship('Comment',
                               backref=db.backref('tweet', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    # 喜欢推特的人
    liked_users = db.relationship('User',
                                  secondary='user_like_tweet',
                                  lazy='dynamic')

    # 收藏推特的人
    collected_users = db.relationship('User',
                                      secondary='user_collect_tweet',
                                      lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        truncate = partial(
            current_app.jinja_env.filters['truncate'],
            current_app.jinja_env)
        target.abstract = truncate(value, length=200)
        # todo target.body_html

    @property
    def like_count(self):
        return self.liked_users.count_all()

    @property
    def collect_count(self):
        return self.collected_users.count_all()

    @property
    def comment_count(self):
        return self.comments.count_all()

    def dumps(self):
        data = {
            'id': self.id,
            'body': self.body,
            'body_html': self.body_html,
            'created': timesince(self.created),
            'like_count': self.like_count,
            'collect_count': self.collect_count,
            'comment_count': self.comment_count,
            'url': url_for('api.tweets', tweet_id=self.id, _external=True),
            'author': self.author.dumps()
        }
        user = get_current_user()
        if user is not None:
            data['is_liked'] = user.is_like_tweet(self)
            data['is_collected'] = user.is_collect_tweet(self)
        return data

    @staticmethod
    def loads(data):
        body = data.get('body')
        if body is None or body.strip() == '':
            raise ValueError('tweet does not have a body')
        return Tweet(body=body)

    def __repr__(self):
        return f'<Tweet {self.id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweets.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    created = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    parent = db.relationship('Comment',
                             remote_side=[id],
                             backref=db.backref(
                                 'children',
                                 lazy='dynamic',
                                 cascade='all, delete-orphan'),
                             lazy='joined')

    # 喜欢评论的人
    liked_users = db.relationship('User',
                                  secondary='user_like_comment',
                                  lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        pass
        # todo target.body_html

    @property
    def like_count(self):
        return self.liked_users.count_all()

    @property
    def reply_count(self):
        return self.children.count_all()

    def dumps(self):
        data = {
            'id': self.id,
            'body': self.body,
            'body_html': self.body_html,
            'created': timesince(self.created),
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'url': url_for('api.comments',
                           comment_id=self.id,
                           _external=True),
            'author': self.author.dumps()
        }
        if self.parent is not None:
            data['parent'] = {
                'id': self.parent_id,
                'author': self.parent.author.dumps(),
            }
        user = get_current_user()
        if user is not None:
            data['is_liked'] = user.is_like_comment(self)
            data['is_author'] = self.author_id == user.id
        return data

    @staticmethod
    def loads(data):
        body = data.get('body')
        if body is None or body.strip() == '':
            raise ValueError('comment does not have a body')
        comment = Comment(body=body)
        post_id = data.get('post_id')
        if post_id is not None:
            post = Post.query.get(int(post_id))
            comment.post = post
        tweet_id = data.get('tweet_id')
        if tweet_id is not None:
            tweet = Tweet.query.get(int(tweet_id))
            comment.tweet = tweet
        parent_id = data.get('parent_id')
        if parent_id is not None:
            parent = Comment.query.get(int(parent_id))
            comment.parent = parent
        author_id = data.get('author_id')
        if author_id is not None:
            author = User.query.get(int(author_id))
            comment.author = author
        return comment

    def __repr__(self):
        return f'<Comment {self.id}>'


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    desc = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class UserLikePost(db.Model):
    __tablename__ = 'user_like_post'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    user = db.relationship('User')
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'),
                        primary_key=True)
    post = db.relationship('Post')
    created = db.Column(db.DateTime(), default=datetime.utcnow)


class UserCollectPost(db.Model):
    __tablename__ = 'user_collect_post'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    user = db.relationship('User')
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'),
                        primary_key=True)
    post = db.relationship('Post')
    favorite_id = db.Column(db.Integer, db.ForeignKey('favorites.id'),
                            primary_key=True)
    favorite = db.relationship('Favorite')
    created = db.Column(db.DateTime(), default=datetime.utcnow)


class UserLikeComment(db.Model):
    __tablename__ = 'user_like_comment'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    user = db.relationship('User')
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                           primary_key=True)
    comment = db.relationship('Comment')
    created = db.Column(db.DateTime(), default=datetime.utcnow)


class UserLikeTweet(db.Model):
    __tablename__ = 'user_like_tweet'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    user = db.relationship('User')
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweets.id'),
                         primary_key=True)
    tweet = db.relationship('Tweet')
    created = db.Column(db.DateTime(), default=datetime.utcnow)


class UserCollectTweet(db.Model):
    __tablename__ = 'user_collect_tweet'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    user = db.relationship('User')
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweets.id'),
                         primary_key=True)
    tweet = db.relationship('Tweet')
    favorite_id = db.Column(db.Integer, db.ForeignKey('favorites.id'),
                            primary_key=True)
    favorite = db.relationship('Favorite')
    created = db.Column(db.DateTime(), default=datetime.utcnow)


class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    desc = db.Column(db.Text)


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                          primary_key=True)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    # post delete
    # 过期自动删除，允许用户删除自己的消息和别人发给自己的消息


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    sender = db.Column(db.String(64), default='system')
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    receiver = db.relationship('User')
    created = db.Column(db.DateTime(), default=datetime.utcnow)


db.event.listen(Post.body, 'set', Post.on_changed_body)
db.event.listen(Tweet.body, 'set', Tweet.on_changed_body)

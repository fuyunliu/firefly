# -*- coding: utf-8 -*-

import json
from flask import Blueprint, g, jsonify, request
from flask_httpauth import HTTPTokenAuth
from .users import UserAPI, UserPostAPI, UserTweetAPI, UserCommentAPI, \
    UserFavoriteAPI, UserLikeAPI, UserCollectAPI
from .posts import PostAPI, PostCommentAPI, PostLikeAPI, PostCollectAPI
from .tweets import TweetAPI
from .comments import CommentAPI
from .errors import unauthorized, forbidden
from ..models import User

api = Blueprint('api', __name__)
auth = HTTPTokenAuth()


@auth.verify_token
def verify_token(token):
    g.current_user = User.verify_auth_token(token)
    # g.current_user = User.query.get(504)
    return g.current_user is not None


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.after_request
@auth.login_required
def after_request(response):
    data = json.loads(response.get_data())
    data['token'] = g.current_user.generate_auth_token()
    response.set_data(json.dumps(data))
    return response


@api.route('/tokens', methods=['GET', 'POST'])
def create_token():
    print(request.blueprint)
    print(request.endpoint)
    return jsonify({})


user_view = UserAPI.as_view('users')
api.add_url_rule(
    rule='/users',
    defaults={'user_id': None},
    view_func=user_view,
    methods=['GET']
)
api.add_url_rule(
    rule='/users',
    view_func=user_view,
    methods=['POST']
)
api.add_url_rule(
    rule='/users/<int:user_id>',
    view_func=user_view,
    methods=['GET', 'PUT', 'DELETE']
)

post_view = PostAPI.as_view('posts')
api.add_url_rule(
    rule='/posts',
    defaults={'post_id': None},
    view_func=post_view,
    methods=['GET']
)
api.add_url_rule(
    rule='/posts',
    view_func=post_view,
    methods=['POST']
)
api.add_url_rule(
    rule='/posts/<int:post_id>',
    view_func=post_view,
    methods=['GET', 'PUT', 'DELETE']
)

tweet_view = TweetAPI.as_view('tweets')
api.add_url_rule(
    rule='/tweets',
    defaults={'tweet_id': None},
    view_func=tweet_view,
    methods=['GET']
)
api.add_url_rule(
    rule='/tweets',
    view_func=tweet_view,
    methods=['POST']
)
api.add_url_rule(
    rule='/tweets/<int:tweet_id>',
    view_func=tweet_view,
    methods=['GET', 'DELETE']
)

api.add_url_rule(
    rule='/posts/<int:post_id>/comments',
    view_func=PostCommentAPI.as_view('post_comment'),
    methods=['GET', 'POST']
)
api.add_url_rule(
    rule='/posts/<int:post_id>/likes',
    view_func=PostLikeAPI.as_view('post_like'),
    methods=['POST', 'DELETE']
)
api.add_url_rule(
    rule='/posts/<int:post_id>/collects',
    view_func=PostCollectAPI.as_view('post_collect'),
    methods=['POST', 'DELETE']
)
api.add_url_rule(
    rule='/comments/<int:comment_id>',
    view_func=CommentAPI.as_view('comments'),
    methods=['GET', 'DELETE']
)
api.add_url_rule(
    rule='/users/<int:user_id>/posts',
    view_func=UserPostAPI.as_view('user_post'),
    methods=['GET']
)
api.add_url_rule(
    rule='/users/<int:user_id>/tweets',
    view_func=UserTweetAPI.as_view('user_tweet'),
    methods=['GET']
)
api.add_url_rule(
    rule='/users/<int:user_id>/comments',
    view_func=UserCommentAPI.as_view('user_comment'),
    methods=['GET']
)
api.add_url_rule(
    rule='/users/<int:user_id>/favorites',
    view_func=UserFavoriteAPI.as_view('user_favorite'),
    methods=['GET']
)
api.add_url_rule(
    rule='/users/<int:user_id>/likes',
    view_func=UserLikeAPI.as_view('user_like'),
    methods=['GET']
)
api.add_url_rule(
    rule='/users/<int:user_id>/collects',
    view_func=UserCollectAPI.as_view('user_collect'),
    methods=['GET']
)

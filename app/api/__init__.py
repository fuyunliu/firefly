from flask import Blueprint, g, jsonify, request
from flask_httpauth import HTTPTokenAuth
from .users import UserAPI, UserPostAPI, UserTweetAPI, UserCommentAPI, \
    UserFavoriteAPI, UserLikeAPI, UserCollectAPI
from .posts import PostAPI, PostCommentAPI, PostLikeAPI, PostCollectAPI
from .tweets import TweetAPI, TweetCommentAPI, TweetLikeAPI, TweetCollectAPI
from .comments import CommentAPI, CommentLikeAPI
from .errors import unauthorized, forbidden
from ..models import User

api = Blueprint('api', __name__)
auth = HTTPTokenAuth()


@auth.verify_token
def verify_token(token):
    data = User.verify_auth_token(token)
    if data is not None:
        if data['type'] == 'refresh' and request.endpoint != 'api.create_token':
            return False
        if data['type'] == 'access' and request.endpoint == 'api.create_token':
            return False
        g.current_user = User.query.get(data['id'])
        return g.current_user is not None
    return False


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/tokens', methods=['POST'])
def create_token():
    access = g.current_user.generate_auth_token()
    refresh = g.current_user.generate_auth_token(expiration=3600 * 24 * 31, token_type='refresh')
    return jsonify({'access': access, 'refresh': refresh})


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
    rule='/tweets/<int:tweet_id>/comments',
    view_func=TweetCommentAPI.as_view('tweet_comment'),
    methods=['GET', 'POST']
)
api.add_url_rule(
    rule='/tweets/<int:tweet_id>/likes',
    view_func=TweetLikeAPI.as_view('tweet_like'),
    methods=['POST', 'DELETE']
)
api.add_url_rule(
    rule='/tweets/<int:tweet_id>/collects',
    view_func=TweetCollectAPI.as_view('tweet_collect'),
    methods=['POST', 'DELETE']
)
api.add_url_rule(
    rule='/comments/<int:comment_id>',
    view_func=CommentAPI.as_view('comments'),
    methods=['GET', 'DELETE']
)
api.add_url_rule(
    rule='/comments/<int:comment_id>/likes',
    view_func=CommentLikeAPI.as_view('comment_like'),
    methods=['POST', 'DELETE']
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

# -*- coding: utf-8 -*-

import json
from flask import Blueprint, g, jsonify
from flask_httpauth import HTTPTokenAuth
from .users import UserAPI
from .posts import PostAPI
from .errors import unauthorized, forbidden
from ..models import User

api = Blueprint('api', __name__)
auth = HTTPTokenAuth()


# @auth.verify_token
def verify_token(token):
    g.current_user = User.verify_auth_token(token)
    return g.current_user is not None


# @auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


# @api.before_request
# @auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


# @api.after_request
# @auth.login_required
def after_request(response):
    data = json.loads(response.get_data())
    data['token'] = g.current_user.generate_auth_token()
    response.set_data(json.dumps(data))
    return response


# @api.route('/tokens', methods=['POST'])
def create_token():
    return jsonify({
        'token': g.current_user.generate_auth_token(),
        'expiration': 3600,
    })


def register_api(view, rule, endpoint, primary_key='id', converter='int'):
    """
    URL                  Method               Description
    =========== ======================= ===============================
    /users               GET                  Gives a list of all users
    /users               POST                 Creates a new user
    /users/<id>          GET                  Shows a single user
    /users/<id>          PUT                  Updates a single user
    /users/<id>          DELETE               Deletes a single user
    =========== ======================= ===============================
    """

    view_func = view.as_view(endpoint)
    api.add_url_rule(f'/{rule}', defaults={primary_key: None},
                     view_func=view_func, methods=['GET'])
    api.add_url_rule(f'/{rule}', view_func=view_func, methods=['POST'])
    api.add_url_rule(f'/{rule}/<{converter}:{primary_key}>',
                     view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])


register_api(UserAPI, 'users', 'user_api', primary_key='user_id')
register_api(PostAPI, 'posts', 'post_api', primary_key='post_id')

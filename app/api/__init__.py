# -*- coding: utf-8 -*-

from flask import Blueprint
from .users import UserAPI
from .posts import PostAPI

api = Blueprint('api', __name__)


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

# -*- coding: utf-8 -*-

from flask.views import MethodView


class CommentAPI(MethodView):

    def delete(self, comment_id):
        pass
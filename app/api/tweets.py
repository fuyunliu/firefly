# -*- coding: utf-8 -*-

from flask import current_app, g, jsonify, request, url_for
from flask.views import MethodView
from .. import db
from ..models import Tweet


class TweetAPI(MethodView):

    def get(self, tweet_id):
        if tweet_id is not None:
            tweet = Tweet.query.get_or_404(tweet_id)
            return jsonify(tweet.dumps())

        size = current_app.config['FIREFLY_PER_PAGE_SIZE']
        max_id = request.args.get('max_id', None, type=int)
        if max_id is None:
            items = Tweet.query.order_by(Tweet.id.desc()).limit(size)
        else:
            items = Tweet.query.filter(Tweet.id < max_id)\
                .order_by(Tweet.id.desc()).limit(size)
        return jsonify({
            'tweets': [t.dumps() for t in items],
            'next': url_for('api.tweets',
                            max_id=min(t.id for t in items),
                            _external=True) if items.count() else None
        })

    def post(self):
        tweet = Tweet.loads(request.json)
        tweet.author = g.current_user
        db.session.add(tweet)
        db.session.commit()
        return jsonify(tweet.dumps()), 201, \
            {'Location': url_for('api.tweets', tweet_id=tweet.id)}

    def delete(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        db.session.delete(tweet)
        db.session.commit()
        return jsonify({'success': 'true'})

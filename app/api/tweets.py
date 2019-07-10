# -*- coding: utf-8 -*-

from flask import current_app, g, jsonify, request, url_for
from flask.views import MethodView
from .. import db
from ..models import Tweet, Comment


class TweetAPI(MethodView):

    def get(self, tweet_id):
        if tweet_id is not None:
            tweet = Tweet.query.get_or_404(tweet_id)
            return jsonify(tweet.dumps())

        size = current_app.config['PER_PAGE_SIZE']
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


class TweetCommentAPI(MethodView):

    def get(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        page = request.args.get('page', 1, type=int)
        pagination = tweet.comments.paginate(
            page,
            per_page=current_app.config['PER_PAGE_SIZE'],
            error_out=False)
        prev = None
        if pagination.has_prev:
            prev = url_for('api.tweet_comment', tweet_id=tweet_id,
                           page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api.tweet_comment', tweet_id=tweet_id,
                           page=page + 1, _external=True)
        return jsonify({
            'comments': [p.dumps() for p in pagination.items],
            'prev': prev,
            'next': next,
            'count': pagination.total
        })

    def post(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        comment = Comment.loads(request.json)
        comment.tweet = tweet
        comment.author = g.current_user
        db.session.add(comment)
        db.session.commit()


class TweetLikeAPI(MethodView):

    def post(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        g.current_user.like_tweet(tweet)
        db.session.commit()

    def delete(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        g.current_user.dislike_tweet(tweet)
        db.session.commit()


class TweetCollectAPI(MethodView):

    def post(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        g.current_user.collect_tweet(tweet)
        db.session.commit()

    def delete(self, tweet_id):
        tweet = Tweet.query.get_or_404(tweet_id)
        g.current_user.discollect_tweet(tweet)
        db.session.commit()

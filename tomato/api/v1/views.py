# -*- coding: utf-8 -*-

import json
from flask import request
from flask import Response
from flask import abort
from tomato.api.core import micro
from tomato.api.v1.core import bp

def jsonify(data):
    """Helper function: jsonify.

    Differ from flask.jsonify: It can wrap list as well.
    """
    data = json.dumps(data)
    response = Response(data)
    response.headers['Content-Type'] = 'application/json'
    response.status = 200
    return response


@bp.route('/subjects/<int:subject_id>')
def get_subject(subject_id):
    """Get subject information."""
    resp = micro.subject.Subject.get_subject(subject_id)
    subject = resp['result']
    if not subject:
        abort(404)
    return jsonify(subject)


@bp.route('/subjects/<int:subject_id>/discussions')
def get_subject_discussions(subject_id):
    """Get subject timeline."""
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.subject.Subject.get_subject(subject_id)
    subject = resp['result']
    if not subject:
        abort(404)
    resp = micro.discussion.Discussion.get_subject_discussions(
        subject_id=subject_id, offset=offset, limit=limit
    )
    discussions = resp['result']
    return jsonify(discussions)


@bp.route('/feeds')
def get_feeds():
    """Get user feeds."""
    user = request.models.get('user')
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.stream.Stream.get_feeds(
        user_id=user['id'],
        offset=offset,
        limit=limit,
    )
    feeds = resp['result']
    return jsonify(feeds)


@bp.route('/discussions/explore')
def get_discussion_exploration():
    """Find some fresh discussions to guide user exploring this project."""
    resp = micro.discussion.Discussion.get_random_discussions()
    return jsonify(resp['result'])

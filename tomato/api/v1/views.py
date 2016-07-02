# -*- coding: utf-8 -*-

import json
from flask import request
from flask import Response
from flask import abort
from werkzeug.datastructures import MultiDict
from tomato.api.core import micro
from tomato.api.v1.core import bp
from tomato.api.forms import DiscussionCommentForm

def json_to_form(data, prefix='', flattened=None):
    if flattened is None:
        flattened = MultiDict()
    if isinstance(data, dict):
        for k, v in data.iteritems():
            inner_prefix = '%s-%s' % (prefix, k) if prefix else k
            json_to_form(v, inner_prefix, flattened)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            inner_prefix = '%s-%d' % (prefix, i)
            json_to_form(v, inner_prefix, flattened)
    else:
        flattened[prefix] = data
    return flattened


def get_json_data():
    return json_to_form(request.get_json())

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


@bp.route('/follows/subjects')
def get_user_followed_subjects():
    user = get_current_user()
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.stream.Stream.get_user_followed_subjects(
        user_id=user['id'],
        offset=offset,
        limit=limit,
    )
    return jsonify(resp['result'])

@bp.route('/follows/subjects/<int:subject_id>', methods=['POST'])
def follow_subject(subject_id):
    user = get_current_user()
    resp = micro.subject.Subject.get_subject(subject_id)
    subject = resp['result']
    if not subject:
        abort(404)
    resp = micro.stream.Stream.follow_subject(
        user_id=user['id'],
        subject_id=subject_id
    )
    return '', 204

@bp.route('/follows/subjects/<int:subject_id>', methods=['DELETE'])
def unfollow_subject(subject_id):
    user = get_current_user()
    resp = micro.subject.Subject.get_subject(subject_id)
    subject = resp['result']
    if not subject:
        abort(404)
    resp = micro.stream.Stream.unfollow_subject(
        user_id=user['id'],
        subject_id=subject_id
    )
    return '', 204


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

@bp.route('/discussions/published')
def get_published_discussions():
    user = get_current_user()
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.discussion.Discussion.get_published_discussions(
        user_id=user['id'],
        offset=offset,
        limit=limit,
    )
    return jsonify(resp['result'])

@bp.route('/discussions/commented')
def get_commented_discussions():
    user = get_current_user()
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.discussion.Discussion.get_commented_discussions(
        user_id=user['id'],
        offset=offset,
        limit=limit,
    )
    return jsonify(resp['result'])

@bp.route('/discussions/<int:discussion_id>')
def get_discussion(discussion_id):
    resp = micro.discussion.Discussion.get_discussion(discussion_id)
    return jsonify(resp['result'])

@bp.route('/discussions/<int:discussion_id>/comments')
def get_discussion_comments(discussion_id):
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.discussion.Discussion.get_discussion_comments(
        discussion_id=discussion_id,
        offset=offset,
        limit=limit,
    )
    return jsonify(resp['result'])

@bp.route('/discussion/<int:discussion_id>/comments>', methods=['POST'])
def add_discussion_comment(discussion_id):
    form = DiscussionCommentForm(get_json_data())
    if not form.validate_on_submit():
        resp = jsonify({'errors': form.errors})
        resp.status = 400
        return resp
    data = form.data
    resp = micro.discussion.Discussion.get_disucssion(discussion_id)
    if not resp['result']:
        abort(404)
    resp = micro.discussion.Discussion.add_discussion_comment(
        discussion_id=discussion_id,
        title=data['title'],
        content=data['content'],
    )
    return jsonify(resp['result'])

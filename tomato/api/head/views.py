# -*- coding: utf-8 -*-

import json
from flask import request
from flask import render_template
from flask import Response
from flask import abort
from flask_login import login_required
from flask_login import current_user
from werkzeug.datastructures import MultiDict
from tomato.api.core import micro
from tomato.api.core import oauth
from tomato.api.core import login
from tomato.api.forms import DiscussionCommentForm
from tomato.api.head.core import bp

class obj(object):
    def __init__(self, dictionary):
        for a, b in dictionary.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [obj(x) if isinstance(x, dict) else x for x in b])
            else:
               setattr(self, a, obj(b) if isinstance(b, dict) else b)

class User(obj):
    @property
    def is_active(self):
        return True
    @property
    def is_authenticated(self):
        return True
    def get_id(self):
        return self.id
    @property
    def is_anonymous(self):
        return False

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
    response.status_code = 200
    return response

def get_current_user():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        abort(401)
    token = token.replace('Bearer ', '')
    resp = micro.account.Account.get_user_by_token(token)
    if not resp['result']:
        abort(401)
    return resp['result']

@bp.errorhandler(401)
def handle_not_authorized(e):
    resp = jsonify({'message': 'not authorized'})
    resp.status_code = 401
    return resp

@bp.errorhandler(400)
def handle_not_authorized(e):
    resp = jsonify({'message': 'bad request'})
    resp.status_code = 400
    return resp

@bp.errorhandler(403)
def handle_not_authorized(e):
    resp = jsonify({'message': 'forbidden'})
    resp.status_code = 403
    return resp

@bp.errorhandler(404)
def handle_not_authorized(e):
    resp = jsonify({'message': 'not found'})
    resp.status_code = 404
    return resp

@bp.errorhandler(500)
def handle_not_authorized(e):
    resp = jsonify({'message': 'internal server error'})
    resp.status_code = 500
    return resp

@bp.errorhandler(502)
def handle_not_authorized(e):
    resp = jsonify({'message': 'bad gateway'})
    resp.status_code = 502
    return resp

@login.request_loader
def load_user_from_request(request):
    user = get_current_user()
    return user and User(user)

@oauth.usergetter
def get_user_for_oauth(username, password, *args, **kwargs):
    resp = micro.account.Account.validate_user(
        username=username,
        password=password,
    )
    return resp['result'] and obj(resp['result'])

@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    resp = micro.account.OAuth2.save_token(
        client_id=request.client.client_id,
        user_id=request.user.id,
        expires_in=token['expires_in'],
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        scopes=token['scope'],
    )
    return obj(resp['result'])

@oauth.tokengetter
def get_token(access_token=None, refresh_token=None):
    if access_token:
        resp = micro.account.OAuth2.get_token_by_access_token(access_token)
        return obj(resp['result'])
    elif refresh_token:
        resp = micro.account.OAuth2.get_token_by_refresh_token(refresh_token)
        return obj(resp['result'])

@oauth.grantgetter
def get_grant(client_id, code):
    resp = micro.account.OAuth2.get_grant(client_id=client_id, code=code)
    return obj(resp['result'])

@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    resp = micro.account.OAuth2.save_grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        scopes=request.scopes,
        user_id=request.user.id,
    )
    return obj(resp['result'])

@oauth.clientgetter
def get_client(client_id):
    resp = micro.account.OAuth2.get_client(client_id=client_id)
    return obj(resp['result'])

@bp.route('/accounts/me')
@login_required
def get_my_account():
    user = get_current_user()
    return jsonify(user)

@bp.route('/oauth/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        resp = micro.account.OAuth2.get_client(client_id)
        return render_template('oauthorize.html', client=resp['result'])
    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'

@bp.route('/oauth/token', methods=['POST'])
@oauth.token_handler
def access_token():
    return

@bp.route('/oauth/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token():
    pass

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
@login_required
def get_user_followed_subjects():
    user = current_user
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.stream.Stream.get_user_followed_subjects(
        user_id=user['id'],
        offset=offset,
        limit=limit,
    )
    return jsonify(resp['result'])

@bp.route('/follows/subjects/<int:subject_id>', methods=['POST'])
@login_required
def follow_subject(subject_id):
    user = current_user
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
@login_required
def unfollow_subject(subject_id):
    user = current_user
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
@login_required
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
@login_required
def get_published_discussions():
    user = current_user
    offset = request.args.get('offset', type=int, default=0)
    limit = request.args.get('limit', type=int, default=20)
    resp = micro.discussion.Discussion.get_published_discussions(
        user_id=user['id'],
        offset=offset,
        limit=limit,
    )
    return jsonify(resp['result'])

@bp.route('/discussions/commented')
@login_required
def get_commented_discussions():
    user = current_user
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

@bp.route('/discussion/<int:discussion_id>/comments', methods=['POST'])
@login_required
def add_discussion_comment(discussion_id):
    form = DiscussionCommentForm(get_json_data())
    if not form.validate_on_submit():
        resp = jsonify({'errors': form.errors})
        resp.status_code = 400
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

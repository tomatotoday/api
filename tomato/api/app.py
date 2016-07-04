# -*- coding: utf-8 -*-

import logging

import click
from flask import Flask

from tomato.api.core import oauth
from tomato.api.core import login
from tomato.api.head import bp

def create_app():
    app = Flask(__name__)

    app.config.from_object('tomato.api.settings')
    app.config.from_envvar('API_SETTINGS', silent=True)
    print('Running application in %s mode' % (app.debug and 'DEBUG' or 'NON-DEBUG'))

    oauth.init_app(app)
    login.init_app(app)

    app.register_blueprint(bp, url_prefix='/HEAD')

    return app


# -*- coding: utf-8 -*-

import logging

import click
from flask import Flask

from tomato.api.core import oauth
from tomato.api.v1 import bp as v1bp

def create_app():
    app = Flask(__name__)

    app.config.from_object('tomato.api.settings')
    app.config.from_envvar('API_SETTINGS', silent=True)
    print('Running application in %s mode' % (app.debug and 'DEBUG' or 'NON-DEBUG'))

    oauth.init_app(app)

    app.register_blueprint(v1bp, url_prefix='/1')

    return app


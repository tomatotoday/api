# -*- coding: utf-8 -*-

from flask import abort
from flask_jsonrpc.proxy import ServiceProxy
from flask_oauthlib.provider import OAuth2Provider

class MicroservicesProxy(ServiceProxy):

    def __call__(self, *args, **kwargs):
        resp = super(MicroservicesProxy, self).__call__(*args, **kwargs)
        if 'result' not in resp:
            print(resp)
            abort(500)
        return resp

class Micro(object):

    def __getattr__(self, service):
        gateway_url = current_app.config['GATEWAY_URL']
        service_url = '%s/%s/jsonrpc' % (gateway_url, service)
        service_proxy = MicroservicesProxy(service_url)
        return service_proxy

micro = Micro()
oauth = OAuth2Provider()

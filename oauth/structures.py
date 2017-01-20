# -*- coding: utf-8 -*-
__author__ = 'licong'

from .exceptions import APIError


class JsonDict(dict):
    '''
    General json object that allows attributes to be bound to and also behaves like a dict.

    >>> jd = JsonDict(a=1, b='test')
    >>> jd.a
    1
    >>> jd.b
    'test'
    >>> jd['b']
    'test'
    >>> jd.c
    Traceback (most recent call last):
      ...
    AttributeError: 'JsonDict' object has no attribute 'c'
    >>> jd['c']
    Traceback (most recent call last):
      ...
    KeyError: 'c'
    '''

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(r"'JsonDict' object has no attribute '%s'" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value


class PrepareHttpObject(object):
    def __init__(self, client, path):
        self.client = client
        self.path = path

    def __getattr__(self, item):
        if item == 'get':
            return HttpObject(self.client, 'get', self.path)
        if item == 'post':
            return HttpObject(self.client, 'post', self.path)

        return PrepareHttpObject(self.client, "%s/%s" % (self.path, item))


class HttpObject(object):
    def __init__(self, client, method, path):
        self.client = client
        self.method = method
        self.path = path

    def __call__(self, args=None, **kwargs):
        from .utils import http_call
        if self.client.is_expired():
            raise APIError('100015', 'access token is revoked')

        final_args = self.client.public_args
        if args:
            final_args = dict(final_args, **args)
        return http_call(
            self.method,
            self.path,
            final_args,
            **kwargs
        )

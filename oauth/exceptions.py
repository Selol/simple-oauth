# -*- coding: utf-8 -*-
__author__ = 'licong'


class APIError(StandardError):
    def __init__(self, error_code, error, request=None):
        self.error_code = error_code
        self.error = error
        self.request = request
        StandardError.__init__(self, error)

    def __str__(self):
        return 'APIError, error_num: %s, error_message %s, request: %s' % (self.error_code, self.error, self.request)

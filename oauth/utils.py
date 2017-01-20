# -*- coding: utf-8 -*-

import requests
import requests.packages.urllib3 as urllib3
import json, urllib, collections, urlparse
from .structures import JsonDict
from .exceptions import APIError

__author__ = 'licong'

urllib3.disable_warnings()


def parse_json(s):
    '''
    Parse json string or jsonp string into JsonDict.
    >>> r = parse_json(r'{"name":"Michael","score":95}')
    >>> r.name
    u'Michael'
    >>> r['score']
    95
    >>> r = parse_json('callback({"name": "licong"})')
    >>> r.name
    'licong'
    '''
    if not s.startswith(('[', '{')):
        s = s.split("(")[1].strip(");\n")
    return json.loads(s, object_hook=lambda pairs: JsonDict(pairs.iteritems()))


def encode_params(**kw):
    '''
    Do url-encode parameters
    >>> encode_params(a=1, b='R&D')
    'a=1&b=R%26D'
    >>> encode_params(a=u'\u4e2d\u6587', b=['A', 'B', 123])
    'a=%E4%B8%AD%E6%96%87&b=A&b=B&b=123'
    '''

    def _encode(L, k, v):
        if isinstance(v, unicode):
            L.append('%s=%s' % (k, urllib.quote(v.encode('utf-8'))))
        elif isinstance(v, str):
            L.append('%s=%s' % (k, urllib.quote(v)))
        elif isinstance(v, collections.Iterable):
            for x in v:
                _encode(L, k, x)
        else:
            L.append('%s=%s' % (k, urllib.quote(str(v))))

    args = []
    for k, v in kw.iteritems():
        _encode(args, k, v)
    return '&'.join(args)


def decode_params(text):
    """
    Decode text, text can be jsonp, jsonp end with ";", json, or query string

    :param text: text to decoded
    :return: class:JsonDict Object

    Usage::
    >>>decode_params('callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );')
    {u'openid': u'YOUR_OPENID', u'client_id': u'YOUR_APPID'}
    >>>decode_params('{"client_id":"YOUR_APPID","openid":"YOUR_OPENID"}')
    {u'openid': u'YOUR_OPENID', u'client_id': u'YOUR_APPID'}
    >>>decode_params('access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14')
    {'access_token': 'FE04************************CCE2', 'expires_in': '7776000', 'refresh_token': '88E4************************BE14'}

    """
    try:
        response_dict = parse_json(text)
    except (IndexError, ValueError):
        qs = urlparse.parse_qs(text)
        response_dict = JsonDict(((k, v[0]) for k, v in qs.iteritems()))

    if not response_dict:
        raise APIError("can't decode text", "%s is not jsonp, json, or qs" % text)

    return response_dict


# Remove keys that are set to None

def remove_none_keys(d):
    none_keys = [k for (k, v) in d.items() if v is None]
    for key in none_keys:
        del d[key]
    return d


def http_call(method, url, args, format_to_json=True, **kwargs):
    args_keyword_map = {'get': 'params', 'post': 'data'}
    kwargs.update({args_keyword_map.get(method): args})
    r = getattr(requests, method)(url, **kwargs)
    if r.status_code != 200:
        r.raise_for_status()

    if format_to_json:
        result = decode_params(r.text)

        # for Weibo, check http://open.weibo.com/wiki/Error_code
        if 'error' in result:
            raise APIError(result.error, r.text, url)

        # for QQ, check http://wiki.connect.qq.com/%E5%85%AC%E5%85%B1%E8%BF%94%E5%9B%9E%E7%A0%81%E8%AF%B4%E6%98%8E
        if 'ret' in result and result.ret != 0:
            raise APIError(result.ret, result.msg, url)

        # for Weixin, check https://open.weixin.qq.com/cgi-bin/showdocument?action=dir_list&t=resource/res_list&verify=1&id=open1419317853&lang=zh_CN
        if 'errcode' in result:
            raise APIError(result.errorcode, result.errmsg, url)

        return result
    return r.text


https://api.weibo.com/oauth2/authorize?scope=None&state=default_state&redirect_uri=https%3A//api.weibo.com/oauth2/default.html&response_type=code&client_id=1718961681
https://api.weibo.com/oauth2/authorize?scope=None&state=default_state&redirect_uri=https%3A//api.weibo.com/oauth2/default.html&response_type=code&client_id=1718961681

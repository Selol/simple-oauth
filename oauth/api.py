# -*- coding: utf-8 -*-
__version__ = '1.0.0'
__author__ = 'licong'

import when
from .structures import PrepareHttpObject
from .utils import encode_params, http_call, remove_none_keys


def format_userinfo(username, avatar, openid):
    """
    Fomate user info
    """
    return {
        'username': username,
        'avatar': avatar,
        'openid': openid,
    }


class OauthClientMixin(object):
    # API DOMAIN
    DOMAIN = None
    AUTH_ENDPOINT = None
    ACCESS_TOKEN_ENDPOINT = None
    OPENID_ENDPOINT = None
    DEFAULT_SCOPE = None
    API_PREFIX = ""

    CLIENT_ID_NAME, CLIENT_SECRET_NAME = 'client_id', 'client_secret'

    def __init__(self, app_id, app_key, redirect_uri=None, **kwargs):
        self.client_id = str(app_id)
        self.client_secret = str(app_key)
        self.redirect_uri = redirect_uri
        self.auth_url = 'https://%s/%s' % (self.DOMAIN, self.AUTH_ENDPOINT)
        self.access_token_url = 'https://%s/%s' % (self.DOMAIN, self.ACCESS_TOKEN_ENDPOINT)
        self.openid_url = 'https://%s/%s' % (self.DOMAIN, self.OPENID_ENDPOINT)
        self.api_url = 'https://%s%s' % (self.DOMAIN, self.API_PREFIX)
        self.access_token = None
        self.refresh_token = None
        self.expires = None
        self.openid = None
        self.set_access_token(**kwargs)

    def get_authorize_url(self, **kwargs):
        """
        return the authorization url that the user should be redirected to.
        Check
        QQ: http://wiki.connect.qq.com/%E4%BD%BF%E7%94%A8authorization_code%E8%8E%B7%E5%8F%96access_token
        Weibo: http://open.weibo.com/wiki/Oauth2/authorize
        """

        # response_type can be token in QQ
        # Check http://wiki.connect.qq.com/%E4%BD%BF%E7%94%A8implicit_grant%E6%96%B9%E5%BC%8F%E8%8E%B7%E5%8F%96access_token
        response_type = kwargs.pop('response_type', 'code')

        state = kwargs.pop('state', 'default_state')
        scope = kwargs.pop('scope', self.__class__.DEFAULT_SCOPE)
        args = {
            self.CLIENT_ID_NAME: self.client_id
        }
        args.update(
            kwargs,
            response_type=response_type,
            redirect_uri=self.redirect_uri,
            state=state,
            scope=scope,
        )
        remove_none_keys(args)
        return '%s?%s' % (self.auth_url, encode_params(**args))

    def request_access_token(self, code):
        """
        return access_token by using code,
        Check
        Weibo: http://open.weibo.com/wiki/Oauth2/authorize
        QQ: http://wiki.connect.qq.com/%E5%BC%80%E5%8F%91%E6%94%BB%E7%95%A5_server-side
        """
        args = {
            self.CLIENT_ID_NAME: self.client_id,
            self.CLIENT_SECRET_NAME: self.client_secret,
        }
        args.update(
            redirect_uri=self.redirect_uri,
            code=code,
            grant_type='authorization_code',
        )
        remove_none_keys(args)
        return http_call('post', self.access_token_url, args)

    def set_access_token(self, access_token=None, expires_in=None, expires=None, refresh_token=None, openid=None):
        self.access_token = access_token
        if expires_in:
            self.expires = when.future(seconds=int(expires_in))
        elif expires:
            self.expires = expires
        self.refresh_token = refresh_token
        self.openid = openid

    def is_expired(self):
        if self.access_token and self.expires is not None:
            return when.now() > self.expires

    def __getattr__(self, items):
        return PrepareHttpObject(self, "%s/%s" % (self.api_url, items))


class QQClient(OauthClientMixin):
    # http://wiki.connect.qq.com/%E5%BC%80%E5%8F%91%E6%94%BB%E7%95%A5_server-side
    DOMAIN = "graph.qq.com"
    AUTH_ENDPOINT = "oauth2.0/authorize"
    ACCESS_TOKEN_ENDPOINT = "oauth2.0/token"
    OPENID_ENDPOINT = "oauth2.0/me"
    DEFAULT_SCOPE = "get_user_info"

    # http://wiki.connect.qq.com/openapi%E8%B0%83%E7%94%A8%E8%AF%B4%E6%98%8E_oauth2-0
    @property
    def public_args(self):
        return dict(
            access_token=self.access_token,
            oauth_consumer_key=self.client_id,
            format='json',
            openid=self.get_openid(),
        )

    # Rewrite to auto set
    def request_access_token(self, code):
        rv = OauthClientMixin.request_access_token(self, code)
        self.set_access_token(rv.access_token, rv.expires_in)

    # http://wiki.connect.qq.com/%E7%A7%BB%E5%8A%A8%E5%BA%94%E7%94%A8%E6%8E%A5%E5%85%A5%E6%B5%81%E7%A8%8B
    def get_openid(self):
        if not self.openid:
            args = dict(
                access_token=self.access_token
            )
            self.openid = http_call('get', self.openid_url, args)['openid']
        return self.openid

    # http://wiki.connect.qq.com/get_user_info
    def get_user_info(self):
        rv = self.user.get_user_info.get()
        return format_userinfo(
            rv['nickname'],
            rv['figureurl_qq_1'],
            self.openid
        )


class WeiboClient(OauthClientMixin):
    DOMAIN = "api.weibo.com"
    # http://open.weibo.com/wiki/Oauth2/authorize
    AUTH_ENDPOINT = "oauth2/authorize"
    # http://open.weibo.com/wiki/OAuth2/access_token
    ACCESS_TOKEN_ENDPOINT = "oauth2/access_token"
    # Currently useless, because we can also get openid when we get access_token, it's different from QQ
    # http://open.weibo.com/wiki/Oauth2/get_token_info
    OPENID_ENDPOINT = "oauth2/get_token_info"

    API_PREFIX = "/2"

    @property
    def public_args(self):
        return dict(
            access_token=self.access_token
        )

    # This step will also get uid, see below.
    # http://open.weibo.com/wiki/OAuth2/access_token
    def request_access_token(self, code):
        rv = OauthClientMixin.request_access_token(self, code)
        self.set_access_token(rv.access_token, rv.expires_in, openid=rv.uid)

    # http://open.weibo.com/wiki/2/users/show
    def get_user_info(self):
        rv = getattr(self.users, 'show.json').get(dict(uid=self.openid))
        return format_userinfo(
            rv['screen_name'],
            rv['avatar_large'],
            self.openid
        )


class WeixinClient(OauthClientMixin):
    """
    # Weixin mobile client do not need redirect_url
    >>> client = WeixinClient('app_id', 'app_key')
    >>> client.request_access_token('code')
    >>> clentt.get_user_info()
    {'username': 'nickname'...}

    or you can
    >>> client = WeixinClient('app_id', 'app_key', access_token='token', openid='openid')
    """

    DOMAIN = 'api.weixin.qq.com'
    ACCESS_TOKEN_ENDPOINT = "sns/oauth2/access_token"
    SCOPE = 'snsapi_userinfo'

    CLIENT_ID_NAME = 'appid'
    CLIENT_SECRET_NAME = 'secret'

    def get_authorize_url(self, **kwargs):
        self.auth_url = 'https://open.weixin.qq.com/connect/qrconnect'
        if 'scope' not in kwargs:
            kwargs['scope'] = 'snsapi_login'
        return OauthClientMixin.get_authorize_url(self, **kwargs)

    @property
    def public_args(self):
        return dict(
            access_token=self.access_token,
            openid=self.openid
        )

    # https://open.weixin.qq.com/cgi-bin/showdocument?action=dir_list&t=resource/res_list&verify=1&id=open1419317853&token=ce7038b1ec5931d4ddf7150ba8eb2246ba3e13e4&lang=zh_CN
    def request_access_token(self, code):
        rv = OauthClientMixin.request_access_token(self, code)
        self.set_access_token(rv.access_token, rv.expires_in, openid=rv.openid)

    # Same url with request_access_token
    def get_user_info(self):
        rv = self.sns.userinfo.get()
        return format_userinfo(
            rv['nickname'],
            rv['headimgurl'],
            self.openid
        )

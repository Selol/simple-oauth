# simple-oauth

简单提供几个社交网站的OAuth2.0功能以及API调用，目前支持QQ，微信

基本用法

```python
from oauth.api import QQClient

QQ_OAUTH = {
    'app_id': "your app id",
    'app_key': "you app key",
    'redirect_uri': "your redirect url"
}

qq_client = QQClient(**QQ_OAUTH)
qq_client.get_authorize_url()
```
将生成的地址输入浏览器，授权后会返回回调地址，并附带code参数，此时根据code参数可获取access_token

```python
qq_client.request_access_token(code)
# 此时可以将qq_client.access_token以及qq_client.expires存储起来，以方便下次使用。
```
如果已有access_token，则可以直接初始化客户端

```python
from oauth.api import QQClient
QQ_OAUTH = {
    'app_id': "your app id",
    'app_key': "you app key",
    'redirect_uri': "your redirect url"，
    'access_token': "your access_token",
    'expires': expires # Datetime.datatime instance
}

qq_client = QQClient(**QQ_OAUTH)
```

## 调用api
初始化客户端后即可开始调用各平台api，以QQ获取用户信息接口举例

详情见：http://wiki.connect.qq.com/get_user_info

url: https://graph.qq.com/user/get_user_info

method: get

params: 公共参数

此时只需将url中的"/"转化为".",进行链式调用

```python
qq_client.user.get_user_info.get()
```
公共参数会自动带上
如果有额外参数，则如下

```python
qq_client.a.b.get({'foo': 1})
```
如请求中需要post文件，则

```python
f = open('./test.png', 'rb')
qq_client.a.b.post({'foo': 1}, files={'pic': f})
```
关键字参数与requests模块中一致。

# flask中使用实例

场景：用户使用oauth登录后，将用户与本系统中的用户关联起来，获取用户的用户名，头像，并存储。

解析: 客户端用户输完密码后，需要用户的openid在本系统上关联用户。通常做法是客户端（app或网页）将openid传过来，但服务端仅凭openid是无法确定openid真实性的，所以需要服务端解析code或者access_token和openid

做法： 根据客户端传来的code或者access_token和openid，确定用户身份， 并存储用户头像和用户名
（客户端获取openid不可取，无法知晓openid的真实性。）

```python

from flask import Flask, abort, request
from oauth.api import QQClient, WeiboClient


app = Flask(__name__)
app.secret_key = "dawdbawda"

QQ_OAUTH = {
    'app_id': "your app id",
    'app_key': "you app key",
    'redirect_uri': "your redirect url"，
}

WEIBO_OAUTH = {
    'app_id': "your app id",
    'app_key': "you app key",
    'redirect_uri': "your redirect url"，
}

qq_client = QQClient(**QQ_OAUTH)
weibo_client = WeiboClient(**WEIBO_OAUTH)

ALLOW_SOURCE = {
    'qq': qq_client,
    'weibo': weibo_client, 
}

@app.route(/oauth/<source>)
def oauth(source):
    if source not in ALLOW_SOURCE:
        abort(404)
    code, access_token, openid = request.args.get('code'), request.args.get('access_token'), request.args.get('openid')
    client = ALLOWED_SOURCE[source]
    if code:
        client.request_access_token(code)
    elif access_token and openid:
        # 这里偷懒了，默认认为客户端传来的access_token总是可用的
        client.set_access_token(access_token, openid=openid, expires_in=24 * 365 * 3600)
    else:
        abort(404)
    user_info = client.get_user_info()

    condition = ((User.openid == user_info['openid']) & (User.type == source))
    user = User.query.filter(condition).first() or User()
    user.username = user_info['username']
    user.avatar = user_info['avatar']
    user.openid = user_info['openid']
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return 'ok'

#! usr/bin/python
"""
默认配置
"""

from datetime import timedelta

# 表示应用程序运行在什么环境上
ENV = None

# 启用或禁用调试模式
DEBUG = None

# 开启测试模式
TESTING = False

# CSRF防护
CSRF_ENABLE = True

# 异常被重新抛出，而不是由应用程序的错误处理程序进行处理。如果没有设置，且TESTING或者DEBUG被开启了，那么这个配置项将被隐式地设置为true。
PROPAGATE_EXCEPTIONS = None

# 当有一个异常发生时，不会弹出请求上下文。如果没有设置，且DEBUG为true的话，那么这个配置项将被设置为true。这个配置项允许调试器对错误的请求数据进行内省，并且通常不需要直接设置。
PRESERVE_CONTEXT_ON_EXCEPTION = None

# 表示一个密钥，它将用于安全地签署会话cookie，并且它能在你的应用程序中用于扩展组件中其他安全相关的需求。它应该是一个很长的随机字符串，尽管Unicode也能被接受。
SECRET_KEY = None

# 如果session.permanent为true，那么cookie的过期时间将会被设置成几秒钟后。这个值类型既能设置为datetime.timedelta，也能设置为int。
PERMANENT_SESSION_LIFETIME = timedelta(days=31)

# 在服务文件时，设置X-Sendfile头而不是使用Flask来服务数据。有些web服务，比如Apache，意识到了这点，并且更加有效地服务数据。这个配置选项仅在使用这种服务器的时候有意义。
USE_X_SENDFILE = False

# 通知应用程序绑定的主机地址和端口。这是子域路由匹配支持所需的。
SERVER_NAME = None

# 通知应用程序，它在应用程序/Web服务器下的安装路径是什么。 如果SESSION_COOKIE_PATH没有设置的话，这个配置项将被用于会话cookie路径。
APPLICATION_ROOT = '/'

# 会话cookie的名称。可以在如下场景更改这个值：你已经拥有一个跟这个名字一模一样的cookie。
SESSION_COOKIE_NAME = 'session'

# 会话cookie将会生效的域匹配规则。如果设置为False，cookie的域将不会被设置。如果没有设置，cookie就会对SERVER_NAME的所有子域生效。
SESSION_COOKIE_DOMAIN = None

# 会话cookie将会生效的路径。如果没有设置，cookie会在APPLICATION_ROOT下生效，或者在/下生效（如果APPLICATION_ROOT没有设置的话）。
SESSION_COOKIE_PATH = None

#  为了安全起见，浏览器将不会允许JavaScript访问被标记为“HTTP only”的cookie。
SESSION_COOKIE_HTTPONLY = True

# 如果cookie被标记为“secure”，那么浏览器将仅仅发送HTTPS请求的cookie。应用程序必须通过HTTPS工作，才会让这个配置项有意义。
SESSION_COOKIE_SECURE = False

# 限制cookie是如何随着外部网站请求发送的。该配置项能够被设置为‘Lax’（推荐）或者‘Strict’。
SESSION_COOKIE_SAMESITE = None

# 当session.permanent为true时，控制cookie是否随每个响应一起发送。一直发送cookie（默认行为）能让会话不容易过期，但是需要使用更多的带宽。非长期存在的会话不受这个配置项的影响。
SESSION_REFRESH_EACH_REQUEST = True

# 传入请求数据的最大字节数。如果没有设置这个配置项，且请求没有指定一个CONTENT_LENGTH，为了安全起见不会有数据被读取。
MAX_CONTENT_LENGTH = None

# 当服务文件时，设置控制缓存最大期限为指定的秒数。能设置为一个int类型的值，也能设置为一个datetime.timedelta类型的值。在应用程序或蓝图的每个文件基础上要重写此值的话，则使用get_send_file_max_age()函数。
SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)

# 尝试访问一个不存在于请求字典中的键，比如args和form，将会返回一个400 Bad Request的错误页面。开启这个配置项将会把这个错误当做一个未处理的异常显示到交互式调试器中。这是一个TRAP_HTTP_EXCEPTIONS衍生的特别版本。如果没有设置，这个选项将在调试模式下开启。
TRAP_BAD_REQUEST_ERRORS = None

# 如果一个HTTPException类型的异常没有对应的处理程序，将重新抛出这个异常，并由交互式调试器进行处理，而不是将其作为一个简单的错误响应进行回执。
TRAP_HTTP_EXCEPTIONS = False

# 日志调试信息追踪如何加载一个模板文件。这可以被用来指出为什么一个模板没有被加载，或者为什么加载了一个错误的模板文件。
EXPLAIN_TEMPLATE_LOADING = False

# 当没有请求上下文时，使用此方案生成外部URL。
PREFERRED_URL_SCHEME = 'http'

# 将对象序列化为ASCII编码的JSON。如果这个配置项是不可用的，JSON会被当做一个Unicode字符串进行返回动作，或者使用jsonify将其编码为UTF-8。当在模板中将JSON渲染给JavaScript时，若不开启这个配置项是会带来安全相关的影响的，因此这个配置项默认是保持开启的。
JSON_AS_ASCII = True

# 以字母顺序对JSON对象的键进行排序。这对于缓存是很有用的，因为不管Python的哈希种子是什么，它都将确保数据以相同的方式进行序列化。虽然不推荐这样做，但是如果你想改进缓存成本的性能，你可以禁用这个配置项。
JSON_SORT_KEYS = True

# jsonify响应将输出新行、空格以及缩进排版，以便容易阅读。这个配置项在调试模式下总是开启的。
JSONIFY_PRETTYPRINT_REGULAR = False

# jsonify响应的mimetype。
JSONIFY_MIMETYPE = 'application/json'

# 当模板有更改时将会重新加载模板。如果没有设置，它会在调试模式下开启。
TEMPLATES_AUTO_RELOAD = None

# cookie头的最大字节数。
MAX_COOKIE_SIZE = 4093


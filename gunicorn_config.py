# gunicorn配置文件

# 绑定的IP和端口
bind = "0.0.0.0:10010"

# 工作进程数
workers = 4

# 工作模式
worker_class = "uvicorn.workers.UvicornWorker"

# 日志配置
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 进程名称前缀
proc_name = "dataweaver"

# 后台运行
daemon = True

# 重载代码时自动重启
reload = True

# 超时设置
timeout = 120

# 最大并发请求数
max_requests = 1000
max_requests_jitter = 50

# 优雅的重启时间
graceful_timeout = 30
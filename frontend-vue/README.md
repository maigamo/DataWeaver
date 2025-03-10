# DataWeaver 前端部署指南

本文档详细说明如何将 DataWeaver 前端项目部署到生产环境中的 Nginx 服务器上。

## 构建项目

1. 在项目根目录下执行构建命令：

```bash
npm run build
```

2. 构建完成后，将在 `dist` 目录下生成生产环境的静态文件。

## Nginx 配置

### 基础配置

1. 将 `dist` 目录下的所有文件复制到 Nginx 的静态资源目录（例如：`/usr/share/nginx/html`）

2. 配置 Nginx 虚拟主机（在 `/etc/nginx/conf.d/` 下创建配置文件，如 `dataweaver.conf`）：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /usr/share/nginx/html;
    index index.html;

    # 处理 Vue Router 的 history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://backend-server:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存策略
    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # 安全相关的响应头
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';";
}
```

### HTTPS 配置（推荐）

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # SSL 配置优化
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # 现代 SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS 配置（可选）
    add_header Strict-Transport-Security "max-age=63072000" always;

    # 其他配置与 HTTP 部分相同
    ...
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 性能优化

### Gzip 压缩

在 Nginx 配置文件中添加：

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;
```

### 浏览器缓存策略

```nginx
# 静态资源缓存策略
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
    expires 30d;
    add_header Cache-Control "public, no-transform";
}

# HTML 文件不缓存
location ~* \.html$ {
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}
```

## 维护建议

1. 定期更新 Nginx 版本以获取安全补丁
2. 使用 SSL 证书管理工具（如 Certbot）自动更新 HTTPS 证书
3. 配置日志轮转以管理日志文件大小
4. 定期检查 Nginx 错误日志排查潜在问题
5. 使用监控工具（如 Prometheus + Grafana）监控服务器状态

## 故障排查

1. 检查 Nginx 错误日志：
```bash
tail -f /var/log/nginx/error.log
```

2. 检查 Nginx 配置是否正确：
```bash
nginx -t
```

3. 常见问题：
   - 502 Bad Gateway：检查后端服务是否正常运行
   - 404 Not Found：检查文件路径和权限
   - 403 Forbidden：检查文件和目录权限

## 安全建议

1. 定期更新系统和 Nginx 版本
2. 使用强密码和密钥
3. 配置防火墙规则
4. 启用 HTTPS
5. 定期进行安全扫描
6. 配置适当的文件权限

## 注意事项

1. 部署前备份当前配置
2. 在测试环境验证配置
3. 确保域名 DNS 解析正确
4. 保护好 SSL 证书私钥
5. 定期备份配置文件

# SQLWeaver 部署指南

## 系统要求

- Node.js 16+ 或更高版本
- npm 或 yarn（Node.js包管理器）
- 至少 100MB 可用磁盘空间
- 建议 2GB 或更多内存
- 网络连接（用于安装依赖包）

## 安装步骤

### 1. 获取代码

```bash
git clone https://github.com/yourusername/SQLWeaver.git
cd SQLWeaver
```

### 2. 环境配置

#### 2.1 安装依赖

安装前端依赖：
```bash
cd frontend-vue
npm install
```

## 服务配置

### 1. 配置文件说明

项目主要包含以下配置文件：
- `vite.config.js`: 前端开发和构建配置

### 2. 端口配置

默认端口：
- 前端开发服务器：5173

如需修改端口，请在相应文件中更新：
- `vite.config.js`: 修改 server.port 配置项

## 启动服务

### 开发环境

启动前端开发服务器：
```bash
# 进入前端项目目录
cd frontend-vue
npm run dev
```

### 生产环境

1. 构建前端项目：
```bash
cd frontend-vue
npm run build
```

2. 部署静态文件：
将 `frontend-vue/dist` 目录下的文件部署到您的Web服务器（如Nginx、Apache等）。

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your_domain.com;

    root /path/to/SQLWeaver/frontend-vue/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 常见问题

1. **前端开发服务器无法启动**
   - 检查端口5173是否被占用
   - 确保已安装所有依赖
   - 检查Node.js版本是否满足要求

2. **构建失败**
   - 检查是否有语法错误或依赖问题
   - 确保node_modules目录存在且完整
   - 尝试删除node_modules并重新安装依赖

## 维护和更新

1. 更新依赖：
```bash
cd frontend-vue
npm update
```

2. 清理构建缓存：
```bash
cd frontend-vue
npm run clean
# DataWeaver
一键部署的轻量级资源共享平台，适合定制化多的项目，适配多分支自定义生成数据库造数脚本，提供各类资源文件资源共享与自身平台的对外服务的数据统计。
提供了一个简单的Web界面，允许不同用户通过参数配置生成所需的SQL脚本，允许不同用户上传资源文件，支持文件自动过期和存储空间管理。


## 功能特点

- 支持自定义用户数量和起始索引
- 支持配置部门信息和用户分布
- 支持设置设备数量和起始索引
- 提供Web界面，操作简单直观
- 生成的脚本自动打包为ZIP文件
- 用户管理系统，支持多角色权限控制
- RESTful API接口，支持系统集成
- 支持多分支管理和模板定制
- 提供数据统计和可视化功能
- 支持文件自动过期和存储空间管理（默认关闭）

## 文件清理功能

系统提供了自动清理过期文件的功能（默认关闭），可以通过以下步骤开启：

1. 在 `tasks/scheduler.py` 文件中，将 `ENABLE_CLEANUP` 变量设置为 `True`：
```python
ENABLE_CLEANUP = True
```

2. 清理功能配置说明：
   - 默认每天凌晨2点执行清理
   - 默认清理2年前的文件
   - 清理配置可在 `tasks/cleanup.py` 中修改

## 系统架构

### 前端技术栈
- Vue 3 + TypeScript
- Vite构建工具
- Vue Router路由管理
- Element Plus UI组件库
- ECharts图表可视化

### 后端技术栈
- FastAPI框架
- SQLite数据库
- JWT认证机制
- OAuth2授权流程

## 环境要求

- Node.js 16+
- Python 3.8+
- npm 或 yarn
- 至少 100MB 可用磁盘空间
- 建议 2GB 或更多内存
- 网络连接（用于安装依赖包）

## 快速部署

### Docker部署（推荐）

1. 构建Docker镜像：
```bash
docker build -t dataweaver .
```

2. 运行容器：
```bash
docker run -d -p 8000:8000 -p 5173:5173 dataweaver
```

### 手动部署

1. 克隆项目：
```bash
git clone https://github.com/maigamo/DataWeaver.git
cd DataWeaver
```

2. 安装依赖：
```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend-vue
npm install
```

3. 构建前端：
```bash
cd frontend-vue
npm run build
```

### 启动服务

项目支持两种启动方式：

#### 1. 使用uvicorn（单进程模式）

适合开发环境和小规模部署：

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 10010 --reload
```

特点：
- 单进程运行，适合开发调试
- 支持热重载，代码修改后自动重启
- 资源占用较少

#### 2. 使用gunicorn（多进程模式）

适合生产环境部署：

```bash
gunicorn -c gunicorn_config.py app:app
```

特点：
- 多进程运行，充分利用多核CPU
- 更好的并发处理能力
- 内置负载均衡
- 进程管理和故障恢复

### 配置Systemd服务（Linux）：
```bash
# 创建服务文件
sudo nano /etc/systemd/system/dataweaver.service

# 添加以下内容
[Unit]
Description=DataWeaver Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/DataWeaver
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

5. 启动服务：
```bash
sudo systemctl enable dataweaver
sudo systemctl start dataweaver
```

## 端口配置

### 前端端口修改

在 `frontend-vue/vite.config.ts` 中添加：
```typescript
export default defineConfig({
  server: {
    port: 10086,
    proxy: {
      '/api': {
        target: 'http://localhost:10010',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  plugins: [vue()]
})
```

### 后端端口修改

在 `app.py` 中修改：
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=10010, reload=True)
```

### 前端接口配置

前端项目中的API请求会通过Vite的代理配置自动转发到后端服务。所有的API请求都应该以`/api`作为前缀，例如：

```typescript
// 示例API请求
axios.get('/api/users')
// 将被代理到 http://localhost:10010/users
```

## 访问系统

系统默认访问地址：http://localhost:10086

### 登录要求

- 用户管理系统默认需要登录才能访问
- 未登录用户将自动跳转到登录页面
- 只有超级管理员和普通管理员角色的用户可以访问用户管理系统

### 权限控制

系统采用基于角色的权限控制机制：

#### 普通用户
- 仅可访问文档下载页面
- 可以浏览和下载公开文档

#### 内部用户
- 可访问文档下载页面
- 可访问SQL文件下载页面
- 可以浏览和下载内部文档和SQL文件

#### 操作员
- 可访问文档下载页面
- 可访问SQL文件下载页面
- 可使用SQL生成功能
- 可上传文档
- 不可访问用户管理和系统配置

#### 超级管理员
- 可访问系统所有功能模块
- 包括用户管理、权限配置
- 可管理所有用户的文档和SQL文件
- 可进行系统配置和维护

## 数据统计功能

系统提供了丰富的数据统计和可视化功能：

- 总体使用情况统计
  - 脚本生成总次数
  - 活跃用户数量
  - 今日生成次数
  - 下载服务次数

- 下载统计分析
  - 支持按天、按月统计下载量
  - 资源文件与脚本下载量对比
  - 下载趋势可视化展示

- 趋势分析
  - 支持7天、30天、90天数据趋势
  - 按月统计数据分析
  - 可视化图表展示

- 用户行为分析
  - 按小时统计操作频率
  - 按星期统计使用趋势
  - 热力图展示使用时段分布

- 模板使用分析
  - 各模板使用占比
  - 饼图展示分布情况

## 存储管理

- 文件自动过期机制
  - 文件默认保留期限为2年
  - 系统自动清理过期文件
  - 支持查看文件剩余保留时间

- 磁盘空间管理
  - 实时显示系统剩余空间
  - 存储空间使用统计
  - 支持设置预警阈值
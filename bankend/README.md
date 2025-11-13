# Skopeo工具后端API

这是Skopeo工具的后端API服务，提供镜像操作的RESTful接口，采用模块化设计，易于扩展和维护。

## 项目结构

```
bankend/
├── app.py                 # 应用主入口
├── config.py              # 配置管理
├── requirements.txt        # 依赖列表
├── routers/              # 路由模块
│   ├── __init__.py
│   └── skopeo_router.py  # Skopeo相关API路由
├── services/             # 服务模块
│   ├── __init__.py
│   └── image_sync_service.py  # 镜像同步服务
└── utils/               # 工具模块
    ├── __init__.py
    ├── logger.py        # 日志工具
    └── skopeo_utils.py  # Skopeo命令封装
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

### 方法一：使用启动脚本（推荐）

```bash
python run.py
```

启动脚本支持以下参数：

```bash
python run.py --help
```

常用示例：

```bash
# 指定端口
python run.py --port 9000

# 指定日志文件
python run.py --log-file /var/log/skopeo-api.log

# 指定日志级别
python run.py --log-level DEBUG

# 指定Skopeo超时时间
python run.py --skopeo-timeout 300
```

### 方法二：直接运行应用

```bash
python app.py
```

服务将在 `http://localhost:8080` 上启动。

## 环境变量

可以通过以下环境变量配置服务：

- `PORT`: 服务端口，默认为8080
- `HOST`: 服务主机，默认为0.0.0.0
- `SKOPEO_TIMEOUT`: Skopeo命令超时时间（秒），默认为120
- `SKOPEO_PATH`: Skopeo命令路径，默认为skopeo
- `LOG_LEVEL`: 日志级别，默认为INFO
- `LOG_FILE`: 日志文件路径，默认输出到控制台
- `TEMP_DIR`: 临时文件目录，默认为/tmp/skopeo-tools

## API接口

### 镜像检查

**POST /api/inspect**

检查指定镜像的详细信息。

请求体示例：
```json
{
    "imageName": "docker://library/nginx:latest",
    "raw": false,
    "config": false,
    "options": {}
}
```

### 镜像复制

**POST /api/copy**

复制镜像从一个仓库到另一个仓库。

请求体示例：
```json
{
    "sourceImage": "docker://library/nginx:latest",
    "destinationImage": "docker://myregistry.com/nginx:latest",
    "options": {
        "all": false,
        "quiet": false
    }
}
```

### 列出镜像标签

**POST /api/list-tags**

获取仓库中所有可用的标签列表。

请求体示例：
```json
{
    "repository": "docker://library/nginx",
    "options": {
        "useStream": false,
        "countOnly": false,
        "page": 0,
        "limit": 50
    }
}
```

### 同步镜像

**POST /api/sync**

同步指定的镜像列表。

请求体示例：
```json
{
    "source": "docker://library/nginx",
    "destination": "docker://myregistry.com/nginx",
    "options": {
        "all": false,
        "scoped": false
    }
}
```

### 从文件同步镜像

**POST /api/sync/file**

从上传的文件中读取镜像列表并同步。

请求参数：
- image_list: 包含镜像列表的文件（表单文件）
- destination_registry: 目标仓库地址（表单字段）
- source_registry: 源仓库地址（可选，表单字段）
- src_creds: 源仓库认证信息（可选，表单字段）
- dest_creds: 目标仓库认证信息（可选，表单字段）

### 删除镜像

**POST /api/delete**

删除指定的镜像。

请求体示例：
```json
{
    "imageName": "docker://myregistry.com/nginx:latest",
    "options": {}
}
```

### 代理API

以下API用于模拟镜像代理功能：

- **POST /api/proxy/initialize**: 初始化代理
- **POST /api/proxy/open-image**: 打开镜像
- **POST /api/proxy/get-manifest**: 获取清单
- **POST /api/proxy/get-config**: 获取配置
- **POST /api/proxy/get-blob**: 获取数据块

### 获取日志文件

**GET /api/logs/<filename>**

获取指定日志文件的内容。

## 注意事项

1. 确保系统已安装skopeo工具并添加到PATH环境变量
2. 确保对源仓库和目标仓库有适当的访问权限
3. 目标仓库需要提前创建好命名空间

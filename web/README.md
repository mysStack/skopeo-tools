# Skopeo Web UI

这是一个基于 Vue 3 和 Element Plus 的 Web UI，用于与 Skopeo 命令行工具交互。

## 功能特性

- 镜像检查 (Inspect)
- 镜像复制 (Copy)
- 镜像标签列表 (List Tags)
- 镜像同步 (Sync)
- 镜像删除 (Delete)

## 技术栈

- Vue 3
- Element Plus UI 组件库
- Axios (HTTP 客户端)
- Vite (构建工具)

## 安装与运行

1. 安装依赖:
```bash
npm install
```

2. 启动开发服务器:
```bash
npm run dev
```

3. 构建生产版本:
```bash
npm run build
```

4. 预览生产版本:
```bash
npm run preview
```

## API 代理配置

开发环境已配置代理，将 `/api` 请求转发到 `http://localhost:8080`。如果您的 Skopeo API 服务器运行在不同的端口或地址，请修改 `vite.config.js` 中的代理配置。

## 使用说明

### 镜像检查
- 输入镜像名称，格式为 `transport://reference` (例如: `docker://registry.example.com/image:tag`)
- 可选择输出原始清单或配置信息
- 点击"检查镜像"按钮获取镜像详细信息

### 镜像复制
- 输入源镜像和目标镜像
- 可配置多架构处理方式
- 可选择静默模式或复制所有标签
- 点击"复制镜像"按钮执行复制操作

### 镜像标签列表
- 输入仓库地址
- 点击"获取标签列表"按钮
- 查看仓库中的所有可用标签

### 镜像同步
- 选择源类型 (docker, dir, yaml)
- 输入源地址
- 选择目标类型 (docker, dir)
- 输入目标地址
- 配置同步选项
- 点击"同步镜像"按钮执行同步操作

### 镜像删除
- 输入要删除的镜像名称
- 点击"删除镜像"按钮
- 确认删除操作

## 注意事项

- 此 Web UI 需要配合 Skopeo API 服务器使用
- 目前仅实现了基本的 Skopeo 命令功能
- 实验性功能 (如 experimental-image-proxy) 尚未完全集成

## 开发

如需扩展功能或修复问题，请参考 Vue 3 和 Element Plus 官方文档:
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)

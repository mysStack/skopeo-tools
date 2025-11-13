#!/usr/bin/env python3
"""
Skopeo API服务启动脚本
"""
import os
import sys
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动Skopeo API服务")
    parser.add_argument("--host", default=None, help="服务主机地址")
    parser.add_argument("--port", type=int, default=None, help="服务端口")
    parser.add_argument("--log-level", default=None, help="日志级别")
    parser.add_argument("--log-file", default=None, help="日志文件路径")
    parser.add_argument("--skopeo-timeout", type=int, default=None, help="Skopeo命令超时时间(秒)")

    args = parser.parse_args()

    # 设置环境变量
    if args.host:
        os.environ["HOST"] = args.host
    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    if args.log_file:
        os.environ["LOG_FILE"] = args.log_file
    if args.skopeo_timeout:
        os.environ["SKOPEO_TIMEOUT"] = str(args.skopeo_timeout)

    # 导入并运行应用
    from app import app
    import uvicorn

    # 从环境变量或参数获取配置
    host = args.host or os.getenv("HOST", "0.0.0.0")
    port = args.port or int(os.getenv("PORT", "8080"))

    print(f"启动Skopeo API服务在 http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()

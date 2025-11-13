#!/usr/bin/env python3
"""
测试多架构处理功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bankend.utils.skopeo_utils import execute_skopeo

async def test_multiarch():
    # 测试不同多架构选项
    test_cases = [
        {
            "name": "默认多架构处理",
            "args": ["docker://docker.io/library/hello-world:latest", "docker://localhost:5000/test/hello-world:latest"]
        },
        {
            "name": "全部多架构处理",
            "args": ["docker://docker.io/library/hello-world:latest", "docker://localhost:5000/test/hello-world:latest"],
            "multi_arch": "all"
        },
        {
            "name": "仅索引多架构处理",
            "args": ["docker://docker.io/library/hello-world:latest", "docker://localhost:5000/test/hello-world:latest"],
            "multi_arch": "index-only"
        }
    ]

    for case in test_cases:
        print(f"测试: {case['name']}")
        try:
            # 模拟前端传递的选项
            options = {}
            if "multi_arch" in case:
                options["multiArch"] = case["multi_arch"]

            # 构建参数列表
            args = case["args"].copy()

            # 添加多架构选项
            if options.get("multiArch"):
                args.insert(0, f"--multi-arch={options.get('multiArch')}")

            print(f"执行命令: skopeo copy {' '.join(args)}")

            # 注意：这里不实际执行命令，只是打印命令
            # 实际执行需要运行中的 Docker 注册表
            print("命令构建成功\n")

        except Exception as e:
            print(f"错误: {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(test_multiarch())

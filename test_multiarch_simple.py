#!/usr/bin/env python3
"""
测试多架构处理功能 - 简化版
"""

def test_multiarch_options():
    """测试多架构选项的正确构建"""
    # 测试不同多架构选项
    test_cases = [
        {
            "name": "默认多架构处理",
            "args": ["docker://docker.io/library/hello-world:latest", "docker://localhost:5000/test/hello-world:latest"],
            "expected": "docker://docker.io/library/hello-world:latest docker://localhost:5000/test/hello-world:latest"
        },
        {
            "name": "全部多架构处理",
            "args": ["docker://docker.io/library/hello-world:latest", "docker://localhost:5000/test/hello-world:latest"],
            "multi_arch": "all",
            "expected": "--multi-arch=all docker://docker.io/library/hello-world:latest docker://localhost:5000/test/hello-world:latest"
        },
        {
            "name": "仅索引多架构处理",
            "args": ["docker://docker.io/library/hello-world:latest", "docker://localhost:5000/test/hello-world:latest"],
            "multi_arch": "index-only",
            "expected": "--multi-arch=index-only docker://docker.io/library/hello-world:latest docker://localhost:5000/test/hello-world:latest"
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

            # 构建完整命令
            command = f"skopeo copy {' '.join(args)}"

            print(f"预期命令: {case['expected']}")
            print(f"实际命令: {' '.join(args)}")
            print(f"完整命令: {command}")

            # 验证结果
            if ' '.join(args) == case['expected']:
                print("测试通过\n")
            else:
                print("测试失败\n")

        except Exception as e:
            print(f"错误: {str(e)}\n")

if __name__ == "__main__":
    test_multiarch_options()

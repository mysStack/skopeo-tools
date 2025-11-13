
import os
import sys
import json
import subprocess
import time
import asyncio
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Skopeo API", description="使用skopeo进行镜像操作的API服务")

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 执行skopeo命令的辅助函数
async def execute_skopeo(command: str, args: List[str]) -> str:
    """执行skopeo命令并返回输出"""
    start_time = time.time()
    full_command = f"skopeo {command} {' '.join(args)}"
    print(f"[执行命令] {full_command}")

    try:
        process = await asyncio.create_subprocess_shell(
            full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # 将字节转换为字符串
        stdout_str = stdout.decode('utf-8') if stdout else ""
        stderr_str = stderr.decode('utf-8') if stderr else ""

        duration = int((time.time() - start_time) * 1000)
        print(f"[命令完成] {full_command} (耗时: {duration}ms)")

        if stderr_str and "warning" not in stderr_str:
            print(f"Skopeo stderr: {stderr_str}")

        if process.returncode != 0:
            error_message = f"执行skopeo命令失败: {stderr_str}"
            raise HTTPException(status_code=500, detail=error_message)

        return stdout_str
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        print(f"[命令失败] {full_command} (耗时: {duration}ms)")
        print(f"Skopeo error: {str(e)}")

        # 提供更详细的错误信息
        error_message = f"执行skopeo命令失败: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

# 流式执行skopeo命令的辅助函数（用于长时间运行的操作）
async def stream_skopeo(command: str, args: List[str]):
    """流式执行skopeo命令并生成输出"""
    start_time = time.time()
    full_command = f"skopeo {command} {' '.join(args)}"
    print(f"[流式处理开始] {full_command}")

    process = await asyncio.create_subprocess_shell(
        full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    output_data = ""

    async def read_stream(stream, is_error=False):
        nonlocal output_data
        while True:
            line = await stream.readline()
            if not line:
                break
            # 将字节转换为字符串
            line_str = line.decode('utf-8')
            if is_error:
                error_chunk = f"ERROR: {line_str}"
                print(f"[流式处理错误] {error_chunk}")
                yield error_chunk
            else:
                output_data += line_str
                yield line_str

    async def generate_output():
        # 合并标准输出和错误输出
        async for output in read_stream(process.stdout):
            yield output
        async for error in read_stream(process.stderr, is_error=True):
            yield error

        # 等待进程完成
        await process.wait()
        duration = int((time.time() - start_time) * 1000)
        print(f"[流式处理完成] {full_command} (耗时: {duration}ms, 退出代码: {process.returncode})")

        if process.returncode != 0:
            yield f"\n进程退出，代码: {process.returncode}"
        else:
            # 尝试解析输出并记录标签数量
            try:
                json_data = json.loads(output_data.strip())
                if "Tags" in json_data:
                    print(f"[解析成功] 获取到 {len(json_data['Tags'])} 个标签")
            except:
                print("[解析失败] 无法解析JSON输出")

    return StreamingResponse(
        generate_output(),
        media_type="text/plain; charset=utf-8"
    )

# 镜像检查
@app.post("/api/inspect")
async def inspect_image(request: Request):
    data = await request.json()
    image_name = data.get("imageName")
    raw = data.get("raw", False)
    config = data.get("config", False)
    options = data.get("options", {})

    # 添加调试日志
    print(f"接收到的请求体: {json.dumps(data)}")

    if not image_name:
        raise HTTPException(status_code=400, detail="镜像名称是必需的")

    try:
        # 构建skopeo inspect命令参数
        args = [image_name]

        # 添加选项参数
        print("检查原始属性:")
        print(f"raw属性值: {raw}")
        print(f"config属性值: {config}")
        print(f"options对象: {json.dumps(options)}")

        if raw:
            args.append("--raw")
            print("添加了--raw参数")

        if config:
            args.append("--config")
            print("添加了--config参数")

        print(f"最终参数列表: {json.dumps(args)}")

        # 执行skopeo inspect命令
        output = await execute_skopeo("inspect", args)

        # 如果是原始输出，直接返回字符串
        if options.get("raw"):
            return PlainTextResponse(content=output.strip())
        else:
            # 尝试解析JSON输出
            try:
                json_data = json.loads(output.strip())
                return json_data
            except:
                # 如果解析失败，返回原始文本
                return PlainTextResponse(content=output.strip())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 镜像复制
@app.post("/api/copy")
async def copy_image(request: Request):
    data = await request.json()
    source_image = data.get("sourceImage")
    destination_image = data.get("destinationImage")
    options = data.get("options", {})

    if not source_image or not destination_image:
        raise HTTPException(status_code=400, detail="源镜像和目标镜像都是必需的")

    try:
        # 构建skopeo copy命令参数
        args = [source_image, destination_image]

        # 添加选项参数
        if options.get("all"):
            args.insert(0, "--all")

        if options.get("quiet"):
            args.insert(0, "--quiet")

        # 执行skopeo copy命令
        output = await execute_skopeo("copy", args)

        # 返回成功结果
        return {
            "success": True,
            "message": f"成功将镜像从 {source_image} 复制到 {destination_image}",
            "output": output.strip()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 列出标签
@app.post("/api/list-tags")
async def list_tags(request: Request):
    data = await request.json()
    repository = data.get("repository")
    options = data.get("options", {})
    start_time = time.time()

    if not repository:
        raise HTTPException(status_code=400, detail="仓库地址是必需的")

    # 检查skopeo是否可用
    try:
        process = await asyncio.create_subprocess_shell(
            "which skopeo",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail="Skopeo命令不可用，请确保已安装skopeo并将其添加到系统PATH中")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Skopeo命令不可用，请确保已安装skopeo并将其添加到系统PATH中")

    print(f"[开始处理] 获取仓库标签: {repository}")

    try:
        # 构建skopeo list-tags命令参数
        args = [repository]

        # 如果只需要获取标签数量，使用inspect命令
        if options and options.get("countOnly"):
            print(f"[获取标签数量] {repository}")
            try:
                process = await asyncio.create_subprocess_shell(
                    f"skopeo inspect --raw {repository}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    text=True
                )
                stdout, stderr = await process.communicate()

                if stderr and "warning" not in stderr:
                    print(f"Skopeo stderr: {stderr}")

                try:
                    json_data = json.loads(stdout.strip())
                    tag_count = len(json_data.get("Tags", []))
                    return {
                        "repository": repository,
                        "tagCount": tag_count
                    }
                except:
                    print(f"[解析失败] 无法解析JSON输出")
                    # 如果解析失败，返回0
                    return {
                        "repository": repository,
                        "tagCount": 0,
                        "error": "无法解析仓库信息"
                    }
            except Exception as e:
                print(f"[获取标签数量失败] {str(e)}")
                raise HTTPException(status_code=500, detail=f"获取标签数量失败: {str(e)}")

        # 对于大型仓库，使用流式处理
        if options and options.get("useStream"):
            print(f"[使用流式处理] {repository}")
            return await stream_skopeo("list-tags", args)

        # 执行skopeo list-tags命令，设置更长的超时时间
        print(f"[执行命令] skopeo list-tags {' '.join(args)}")
        process = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                f"skopeo list-tags {' '.join(args)}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            ),
            timeout=120.0  # 120秒超时
        )

        stdout, stderr = await process.communicate()

        duration = int((time.time() - start_time) * 1000)
        print(f"[命令完成] 获取仓库标签完成 (耗时: {duration}ms)")

        if stderr and "warning" not in stderr:
            print(f"Skopeo stderr: {stderr}")

        # 尝试解析JSON输出
        try:
            json_data = json.loads(stdout.strip())

            # 如果请求包含分页参数，只返回指定范围的标签
            if options and (options.get("page") is not None or options.get("limit") is not None):
                page = options.get("page", 0)
                limit = options.get("limit", 50)
                start_index = page * limit
                end_index = start_index + limit

                # 创建分页结果
                paginated_result = {
                    "repository": json_data.get("repository", repository),
                    "Tags": json_data.get("Tags", [])[start_index:end_index],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": len(json_data.get("Tags", [])),
                        "totalPages": (len(json_data.get("Tags", [])) + limit - 1) // limit
                    }
                }

                return paginated_result
            else:
                # 如果没有分页参数，返回所有标签
                return json_data
        except:
            # 如果解析失败，返回原始文本
            return PlainTextResponse(content=stdout.strip())
    except asyncio.TimeoutError:
        duration = int((time.time() - start_time) * 1000)
        print(f"[请求失败] 获取仓库标签失败 (耗时: {duration}ms): 请求超时")
        raise HTTPException(status_code=500, detail="请求超时，可能是网络连接问题或仓库响应缓慢。请尝试使用流式处理选项。")
    except HTTPException:
        raise
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        print(f"[请求失败] 获取仓库标签失败 (耗时: {duration}ms): {str(e)}")

        # 提供更详细的错误信息
        error_message = str(e)
        if "manifest unknown" in str(e):
            error_message = "仓库中没有找到默认标签(latest)，但这不影响获取所有标签列表。这个错误通常出现在使用inspect命令时，但list-tags命令应该可以正常工作。"

        raise HTTPException(status_code=500, detail=error_message)

# 镜像同步
@app.post("/api/sync")
async def sync_images(request: Request):
    data = await request.json()
    source = data.get("source")
    destination = data.get("destination")
    options = data.get("options", {})

    if not source or not destination:
        raise HTTPException(status_code=400, detail="源和目标都是必需的")

    try:
        # 构建skopeo sync命令参数
        args = [source, destination]

        # 添加选项参数
        if options.get("all"):
            args.insert(0, "--all")

        if options.get("scoped"):
            args.insert(0, "--scoped")

        # 执行skopeo sync命令
        output = await execute_skopeo("sync", args)

        # 返回同步结果
        return {
            "success": True,
            "output": output.strip()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 镜像删除
@app.post("/api/delete")
async def delete_image(request: Request):
    data = await request.json()
    image_name = data.get("imageName")
    options = data.get("options", {})

    if not image_name:
        raise HTTPException(status_code=400, detail="镜像名称是必需的")

    try:
        # 构建skopeo delete命令参数
        args = [image_name]

        # 执行skopeo delete命令
        output = await execute_skopeo("delete", args)

        # 返回成功结果
        return {
            "success": True,
            "message": f"成功删除镜像 {image_name}",
            "output": output.strip()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 代理 API - 初始化
@app.post("/api/proxy/initialize")
async def proxy_initialize():
    # 代理API暂时保留模拟数据，因为skopeo没有直接的代理初始化命令
    return "0.2.8"

# 代理 API - 打开镜像
@app.post("/api/proxy/open-image")
async def proxy_open_image(request: Request):
    data = await request.json()
    image_name = data.get("imageName")

    if not image_name:
        raise HTTPException(status_code=400, detail="镜像名称是必需的")

    # 代理API暂时保留模拟数据
    return 12345

# 代理 API - 获取清单
@app.post("/api/proxy/get-manifest")
async def proxy_get_manifest(request: Request):
    data = await request.json()
    image_id = data.get("imageId")

    if not image_id:
        raise HTTPException(status_code=400, detail="镜像 ID 是必需的")

    # 代理API暂时保留模拟数据
    return "sha256:abcdef123456789"

# 代理 API - 获取配置
@app.post("/api/proxy/get-config")
async def proxy_get_config(request: Request):
    data = await request.json()
    image_id = data.get("imageId")

    if not image_id:
        raise HTTPException(status_code=400, detail="镜像 ID 是必需的")

    # 代理API暂时保留模拟数据
    return {
        "config": {
            "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "Cmd": ["/bin/sh"],
            "ExposedPorts": {"8080/tcp": {}}
        }
    }

# 代理 API - 获取数据块
@app.post("/api/proxy/get-blob")
async def proxy_get_blob(request: Request):
    data = await request.json()
    image_id = data.get("imageId")
    digest = data.get("digest")
    size = data.get("size")

    if not image_id or not digest:
        raise HTTPException(status_code=400, detail="镜像 ID 和摘要都是必需的")

    # 代理API暂时保留模拟数据
    return size or 1024

# 检查skopeo命令是否可用
async def check_skopeo_availability():
    try:
        process = await asyncio.create_subprocess_shell(
            "skopeo --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # 将字节转换为字符串
        stdout_str = stdout.decode('utf-8') if stdout else ""
        stderr_str = stderr.decode('utf-8') if stderr else ""

        if process.returncode == 0:
            print(f"[系统检查] Skopeo版本: {stdout_str.strip()}")
            return True
        else:
            print(f"[系统错误] Skopeo命令不可用: {stderr_str}")
            print(f"[系统错误] 请确保已安装skopeo并将其添加到系统PATH中")
            return False
    except Exception as e:
        print(f"[系统错误] Skopeo命令不可用: {str(e)}")
        print(f"[系统错误] 请确保已安装skopeo并将其添加到系统PATH中")
        return False

# 启动事件
@app.on_event("startup")
async def startup_event():
    print("Skopeo API 服务器启动")

    # 检查skopeo是否可用
    is_skopeo_available = await check_skopeo_availability()
    if not is_skopeo_available:
        print("[警告] Skopeo不可用，某些功能可能无法正常工作")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

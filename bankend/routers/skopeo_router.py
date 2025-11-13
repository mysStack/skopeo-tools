"""
Skopeo API路由模块
"""
import json
import time
import asyncio
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import PlainTextResponse

from config import settings
from utils.logger import setup_logger
from utils.skopeo_utils import (
    execute_skopeo, 
    stream_skopeo, 
    check_skopeo_availability,
    parse_json_output,
    get_tag_count_from_inspect,
    paginate_results
)

logger = setup_logger(__name__)

# 创建路由器
skopeo_router = APIRouter()

@skopeo_router.post("/inspect")
async def inspect_image(request: Request):
    """
    镜像检查API
    """
    data = await request.json()
    image_name = data.get("imageName")
    raw = data.get("raw", False)
    config = data.get("config", False)
    options = data.get("options", {})

    # 添加调试日志
    logger.debug(f"接收到的请求体: {json.dumps(data)}")

    if not image_name:
        raise HTTPException(status_code=400, detail="镜像名称是必需的")

    try:
        # 构建skopeo inspect命令参数
        args = [image_name]

        # 添加选项参数
        logger.debug("检查原始属性:")
        logger.debug(f"raw属性值: {raw}")
        logger.debug(f"config属性值: {config}")
        logger.debug(f"options对象: {json.dumps(options)}")

        if raw:
            args.append("--raw")
            logger.debug("添加了--raw参数")

        if config:
            args.append("--config")
            logger.debug("添加了--config参数")

        logger.debug(f"最终参数列表: {json.dumps(args)}")

        # 执行skopeo inspect命令
        output = await execute_skopeo("inspect", args)

        # 如果是原始输出，直接返回字符串
        if options.get("raw"):
            return PlainTextResponse(content=output.strip())
        else:
            # 尝试解析JSON输出
            try:
                json_data = parse_json_output(output)
                return json_data
            except:
                # 如果解析失败，返回原始文本
                return PlainTextResponse(content=output.strip())
    except HTTPException as e:
        # 如果是manifest unknown错误，尝试获取可用标签
        if "manifest unknown" in str(e.detail):
            try:
                # 尝试获取可用标签
                list_tags_args = [image_name]
                tags_output = await execute_skopeo("list-tags", list_tags_args)
                tags_data = parse_json_output(tags_output)
                
                # 如果有标签，使用第一个标签重新检查
                if "Tags" in tags_data and tags_data["Tags"]:
                    first_tag = tags_data["Tags"][0]
                    # 更新镜像名称，添加标签
                    if ":" not in image_name.split("/")[-1]:
                        tagged_image = f"{image_name}:{first_tag}"
                        args[0] = tagged_image
                        logger.info(f"尝试使用标签 {first_tag} 重新检查镜像: {tagged_image}")
                        output = await execute_skopeo("inspect", args)
                        
                        # 如果是原始输出，直接返回字符串
                        if options.get("raw"):
                            return PlainTextResponse(content=output.strip())
                        else:
                            # 尝试解析JSON输出
                            try:
                                json_data = parse_json_output(output)
                                return json_data
                            except:
                                # 如果解析失败，返回原始文本
                                return PlainTextResponse(content=output.strip())
            except Exception as retry_error:
                logger.error(f"使用标签重试失败: {str(retry_error)}")
        
        raise
    except Exception as e:
        logger.error(f"镜像检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@skopeo_router.post("/copy")
async def copy_image(request: Request):
    """
    镜像复制API
    """
    data = await request.json()
    logger.info(f"请求数据: {data}")
    source_image = data.get("sourceImage")
    destination_image = data.get("destinationImage")
    options = data.get("options", {})
    logger.info(f"选项参数: {options}")
    src_creds = data.get("srcCreds")  # 源认证信息
    dest_creds = data.get("destCreds")  # 目标认证信息

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
            
        # 处理多架构选项
        multi_arch_value = options.get("multiArch")
        logger.info(f"多架构选项: {multi_arch_value}")
        if multi_arch_value:
            # 确保参数被添加到命令开头
            args.insert(0, f"--multi-arch={multi_arch_value}")
            logger.info(f"已添加多架构参数: --multi-arch={multi_arch_value}")
            logger.info(f"当前命令参数: {args}")

        # 执行skopeo copy命令，传入认证信息
        output = await execute_skopeo("copy", args, src_creds, dest_creds)

        # 返回成功结果
        return {
            "success": True,
            "message": f"成功将镜像从 {source_image} 复制到 {destination_image}",
            "output": output.strip()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"镜像复制失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@skopeo_router.post("/list-tags")
async def list_tags(request: Request):
    """
    列出镜像标签API
    """
    data = await request.json()
    repository = data.get("repository")
    options = data.get("options", {})
    start_time = time.time()

    if not repository:
        raise HTTPException(status_code=400, detail="仓库地址是必需的")

    # 检查skopeo是否可用
    try:
        is_available = await check_skopeo_availability()
        if not is_available:
            raise HTTPException(status_code=500, detail="Skopeo命令不可用，请确保已安装skopeo并将其添加到系统PATH中")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Skopeo命令不可用，请确保已安装skopeo并将其添加到系统PATH中")

    logger.info(f"[开始处理] 获取仓库标签: {repository}")

    try:
        # 如果只需要获取标签数量，使用inspect命令
        if options and options.get("countOnly"):
            logger.info(f"[获取标签数量] {repository}")
            return get_tag_count_from_inspect(repository)

        # 对于大型仓库，使用流式处理
        if options and options.get("useStream"):
            logger.info(f"[使用流式处理] {repository}")
            args = [repository]
            return await stream_skopeo("list-tags", args)

        # 执行skopeo list-tags命令，设置更长的超时时间
        logger.info(f"[执行命令] skopeo list-tags {repository}")
        process = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                f"{settings.SKOPEO_PATH} list-tags {repository}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=False
            ),
            timeout=settings.SKOPEO_TIMEOUT
        )

        stdout, stderr = await process.communicate()
        
        # 将字节转换为字符串
        stdout_str = stdout.decode('utf-8') if stdout else ""
        stderr_str = stderr.decode('utf-8') if stderr else ""

        duration = int((time.time() - start_time) * 1000)
        logger.info(f"[命令完成] 获取仓库标签完成 (耗时: {duration}ms)")

        if stderr_str and "warning" not in stderr_str:
            logger.warning(f"Skopeo stderr: {stderr_str}")

        # 尝试解析JSON输出
        try:
            json_data = parse_json_output(stdout_str)

            # 如果请求包含分页参数，只返回指定范围的标签
            if options and (options.get("page") is not None or options.get("limit") is not None):
                page = options.get("page", 0)
                limit = options.get("limit", 50)
                return paginate_results(json_data, page, limit)
            else:
                # 如果没有分页参数，返回所有标签
                return json_data
        except:
            # 如果解析失败，返回原始文本
            return PlainTextResponse(content=stdout_str.strip())
    except asyncio.TimeoutError:
        duration = int((time.time() - start_time) * 1000)
        logger.error(f"[请求失败] 获取仓库标签失败 (耗时: {duration}ms): 请求超时")
        raise HTTPException(status_code=500, detail="请求超时，可能是网络连接问题或仓库响应缓慢。请尝试使用流式处理选项。")
    except HTTPException:
        raise
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        logger.error(f"[请求失败] 获取仓库标签失败 (耗时: {duration}ms): {str(e)}")

        # 提供更详细的错误信息
        error_message = str(e)
        if "manifest unknown" in str(e):
            error_message = "仓库中没有找到默认标签(latest)，但这不影响获取所有标签列表。这个错误通常出现在使用inspect命令时，但list-tags命令应该可以正常工作。"

        raise HTTPException(status_code=500, detail=error_message)

@skopeo_router.post("/sync")
async def sync_images(request: Request):
    """
    镜像同步API
    """
    data = await request.json()
    
    # 检查是新的API格式还是旧的API格式
    if "images" in data:
        # 新格式：从镜像列表同步
        images = data.get("images", [])
        destination_registry = data.get("destination_registry")
        source_registry = data.get("source_registry", "docker.io")
        src_creds = data.get("src_creds")
        dest_creds = data.get("dest_creds")
        
        from services.image_sync_service import ImageSyncService
        
        # 创建同步服务
        sync_service = ImageSyncService()
        
        # 执行同步
        results = await sync_service.sync_images(
            images, destination_registry, source_registry, src_creds, dest_creds
        )
        
        # 统计结果
        total = len(results)
        success_count = sum(1 for success in results.values() if success)
        failed_count = total - success_count
        
        return {
            "success": success_count == total,
            "total": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "log_file": sync_service.logger.handlers[0].baseFilename if sync_service.logger.handlers else None
        }
    else:
        # 旧格式：单个镜像同步
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
            logger.error(f"镜像同步失败: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@skopeo_router.post("/delete")
async def delete_image(request: Request):
    """
    镜像删除API
    """
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
        logger.error(f"镜像删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 代理 API - 初始化
@skopeo_router.post("/proxy/initialize")
async def proxy_initialize():
    """
    代理初始化API（模拟）
    """
    # 代理API暂时保留模拟数据，因为skopeo没有直接的代理初始化命令
    return "0.2.8"

# 代理 API - 打开镜像
@skopeo_router.post("/proxy/open-image")
async def proxy_open_image(request: Request):
    """
    代理打开镜像API（模拟）
    """
    data = await request.json()
    image_name = data.get("imageName")

    if not image_name:
        raise HTTPException(status_code=400, detail="镜像名称是必需的")

    # 代理API暂时保留模拟数据
    return 12345

# 代理 API - 获取清单
@skopeo_router.post("/proxy/get-manifest")
async def proxy_get_manifest(request: Request):
    """
    代理获取清单API（模拟）
    """
    data = await request.json()
    image_id = data.get("imageId")

    if not image_id:
        raise HTTPException(status_code=400, detail="镜像 ID 是必需的")

    # 代理API暂时保留模拟数据
    return "sha256:abcdef123456789"

# 代理 API - 获取配置
@skopeo_router.post("/proxy/get-config")
async def proxy_get_config(request: Request):
    """
    代理获取配置API（模拟）
    """
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
@skopeo_router.post("/proxy/get-blob")
async def proxy_get_blob(request: Request):
    """
    代理获取数据块API（模拟）
    """
    data = await request.json()
    image_id = data.get("imageId")
    digest = data.get("digest")
    size = data.get("size")

    if not image_id or not digest:
        raise HTTPException(status_code=400, detail="镜像 ID 和摘要都是必需的")

    # 代理API暂时保留模拟数据
    return size or 1024

@skopeo_router.post("/sync/file")
async def sync_from_file(
    image_list: UploadFile = File(...),
    destination_registry: str = Form(...),
    source_registry: str = Form("docker.io"),
    src_creds: Optional[str] = Form(None),
    dest_creds: Optional[str] = Form(None)
):
    """
    从文件同步镜像API
    """
    from services.image_sync_service import ImageSyncService

    try:
        # 保存上传的文件
        file_path = f"{settings.TEMP_DIR}/{image_list.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await image_list.read())

        # 创建同步服务
        sync_service = ImageSyncService()

        # 执行同步
        result = await sync_service.sync_from_file(
            file_path, destination_registry, source_registry, src_creds, dest_creds
        )

        return result
    except Exception as e:
        logger.error(f"从文件同步镜像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@skopeo_router.get("/logs/{filename}")
async def get_log_file(filename: str):
    """
    获取日志文件API
    """
    import os

    log_file_path = os.path.join(settings.TEMP_DIR, filename)

    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=404, detail="日志文件不存在")

    try:
        with open(log_file_path, "r") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        logger.error(f"读取日志文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

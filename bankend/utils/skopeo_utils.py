"""
Skopeo工具模块
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Union

from fastapi import HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def execute_skopeo(command: str, args: List[str], src_creds: str = None, dest_creds: str = None) -> str:
    """
    执行skopeo命令并返回输出

    Args:
        command: skopeo命令
        args: 命令参数列表
        src_creds: 源认证信息 (格式: "username:password")
        dest_creds: 目标认证信息 (格式: "username:password")

    Returns:
        命令输出字符串

    Raises:
        HTTPException: 当命令执行失败时
    """
    start_time = time.time()
    
    # 添加认证参数
    if src_creds:
        args.insert(0, f"--src-creds={src_creds}")
    if dest_creds:
        args.insert(0, f"--dest-creds={dest_creds}")
    
    full_command = f"{settings.SKOPEO_PATH} {command} {' '.join(args)}"
    logger.info(f"[执行命令] {full_command}")

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
        logger.info(f"[命令完成] {full_command} (耗时: {duration}ms)")

        if stderr_str and "warning" not in stderr_str:
            logger.warning(f"Skopeo stderr: {stderr_str}")

        if process.returncode != 0:
            error_message = f"执行skopeo命令失败: {stderr_str}"
            logger.error(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        return stdout_str
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        logger.error(f"[命令失败] {full_command} (耗时: {duration}ms)")
        logger.error(f"Skopeo error: {str(e)}")

        # 提供更详细的错误信息
        error_message = f"执行skopeo命令失败: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

async def stream_skopeo(command: str, args: List[str]) -> StreamingResponse:
    """
    流式执行skopeo命令并生成输出

    Args:
        command: skopeo命令
        args: 命令参数列表

    Returns:
        流式响应对象
    """
    start_time = time.time()
    full_command = f"{settings.SKOPEO_PATH} {command} {' '.join(args)}"
    logger.info(f"[流式处理开始] {full_command}")

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
                logger.error(f"[流式处理错误] {error_chunk}")
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
        logger.info(f"[流式处理完成] {full_command} (耗时: {duration}ms, 退出代码: {process.returncode})")

        if process.returncode != 0:
            yield f"\n进程退出，代码: {process.returncode}"
        else:
            # 尝试解析输出并记录标签数量
            try:
                json_data = json.loads(output_data.strip())
                if "Tags" in json_data:
                    logger.info(f"[解析成功] 获取到 {len(json_data['Tags'])} 个标签")
            except:
                logger.warning("[解析失败] 无法解析JSON输出")

    return StreamingResponse(
        generate_output(),
        media_type="text/plain; charset=utf-8"
    )

async def check_skopeo_availability() -> bool:
    """
    检查skopeo命令是否可用

    Returns:
        如果skopeo可用返回True，否则返回False
    """
    try:
        process = await asyncio.create_subprocess_shell(
            f"{settings.SKOPEO_PATH} --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # 将字节转换为字符串
        stdout_str = stdout.decode('utf-8') if stdout else ""
        stderr_str = stderr.decode('utf-8') if stderr else ""

        if process.returncode == 0:
            logger.info(f"[系统检查] Skopeo版本: {stdout_str.strip()}")
            return True
        else:
            logger.error(f"[系统错误] Skopeo命令不可用: {stderr_str}")
            logger.error("[系统错误] 请确保已安装skopeo并将其添加到系统PATH中")
            return False
    except Exception as e:
        logger.error(f"[系统错误] Skopeo命令不可用: {str(e)}")
        logger.error("[系统错误] 请确保已安装skopeo并将其添加到系统PATH中")
        return False

def parse_json_output(output: str) -> Union[Dict, List, str]:
    """
    尝试解析JSON输出，如果失败则返回原始文本

    Args:
        output: 要解析的字符串

    Returns:
        解析后的JSON对象或原始字符串
    """
    try:
        return json.loads(output.strip())
    except:
        return output.strip()

def get_tag_count_from_inspect(repository: str) -> Dict[str, int]:
    """
    通过inspect命令获取标签数量

    Args:
        repository: 仓库地址

    Returns:
        包含仓库和标签数量的字典
    """
    try:
        process = asyncio.run(
            asyncio.create_subprocess_shell(
                f"{settings.SKOPEO_PATH} inspect --raw {repository}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
        )
        stdout, stderr = process.communicate()

        if stderr and "warning" not in stderr:
            logger.warning(f"Skopeo stderr: {stderr}")

        try:
            json_data = json.loads(stdout.strip())
            tag_count = len(json_data.get("Tags", []))
            return {
                "repository": repository,
                "tagCount": tag_count
            }
        except:
            logger.warning("[解析失败] 无法解析JSON输出")
            # 如果解析失败，返回0
            return {
                "repository": repository,
                "tagCount": 0,
                "error": "无法解析仓库信息"
            }
    except Exception as e:
        logger.error(f"[获取标签数量失败] {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签数量失败: {str(e)}")

def paginate_results(data: Dict, page: int = 0, limit: int = 50) -> Dict:
    """
    对结果进行分页处理

    Args:
        data: 包含Tags列表的数据字典
        page: 页码，从0开始
        limit: 每页数量

    Returns:
        分页后的结果字典
    """
    tags = data.get("Tags", [])
    start_index = page * limit
    end_index = start_index + limit

    return {
        "repository": data.get("repository", ""),
        "Tags": tags[start_index:end_index],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(tags),
            "totalPages": (len(tags) + limit - 1) // limit
        }
    }

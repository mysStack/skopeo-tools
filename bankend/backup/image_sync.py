
import os
import subprocess
import logging
from datetime import datetime
from typing import List, Dict, Optional

class ImageSyncer:
    """使用skopeo同步Docker镜像的类"""

    def __init__(self, log_file: Optional[str] = None):
        """
        初始化镜像同步器

        Args:
            log_file: 日志文件路径，如果不指定则输出到控制台
        """
        self.logger = self._setup_logger(log_file)

    def _setup_logger(self, log_file: Optional[str] = None) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('image_sync')
        logger.setLevel(logging.INFO)

        # 清除可能存在的处理器
        logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # 如果指定了日志文件，添加文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        else:
            # 否则添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def read_image_list(self, file_path: str) -> List[str]:
        """
        从文件中读取镜像列表

        Args:
            file_path: 包含镜像列表的文件路径

        Returns:
            镜像名称列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"镜像列表文件不存在: {file_path}")

        with open(file_path, 'r') as f:
            images = [line.strip() for line in f if line.strip()]

        self.logger.info(f"从文件 {file_path} 中读取到 {len(images)} 个镜像")
        return images

    def sync_image(self, source: str, destination: str, 
                   src_creds: Optional[str] = None, 
                   dest_creds: Optional[str] = None) -> bool:
        """
        同步单个镜像

        Args:
            source: 源镜像 (例如: docker://nginx:latest)
            destination: 目标镜像 (例如: docker://myregistry.com/nginx:latest)
            src_creds: 源仓库认证信息 (格式: username:password)
            dest_creds: 目标仓库认证信息 (格式: username:password)

        Returns:
            同步是否成功
        """
        cmd = ["skopeo", "copy"]

        # 添加认证信息
        if src_creds:
            cmd.extend(["--src-creds", src_creds])
        if dest_creds:
            cmd.extend(["--dest-creds", dest_creds])

        # 添加源和目标
        cmd.extend([source, destination])

        self.logger.info(f"开始同步镜像: {source} -> {destination}")

        try:
            # 执行命令
            result = subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )

            self.logger.info(f"镜像同步成功: {source} -> {destination}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"镜像同步失败: {source} -> {destination}")
            self.logger.error(f"错误信息: {e.stderr}")
            return False

    def sync_images(self, images: List[str], destination_registry: str,
                    source_registry: str = "docker.io",
                    src_creds: Optional[str] = None, 
                    dest_creds: Optional[str] = None) -> Dict[str, bool]:
        """
        批量同步镜像

        Args:
            images: 镜像名称列表
            destination_registry: 目标仓库地址
            source_registry: 源仓库地址，默认为docker.io
            src_creds: 源仓库认证信息
            dest_creds: 目标仓库认证信息

        Returns:
            镜像同步结果字典 {镜像名称: 是否成功}
        """
        results = {}

        self.logger.info(f"开始批量同步 {len(images)} 个镜像")
        self.logger.info(f"源仓库: {source_registry}, 目标仓库: {destination_registry}")

        for image in images:
            # 构建源和目标地址
            source = f"docker://{image}" if not image.startswith("docker://") else image
            dest_image = image
            if not dest_image.startswith("docker://"):
                # 如果源镜像没有包含仓库前缀，添加源仓库前缀
                if '/' not in dest_image or not ('.' in dest_image.split('/')[0]):
                    dest_image = f"{source_registry}/{dest_image}"

                # 构建目标镜像地址
                dest_image = f"{destination_registry}/{dest_image.split('/', 1)[-1]}"

            destination = f"docker://{dest_image}"

            # 同步镜像
            success = self.sync_image(source, destination, src_creds, dest_creds)
            results[image] = success

        self.logger.info("批量同步完成")
        return results

    def sync_from_file(self, image_list_file: str, destination_registry: str,
                      source_registry: str = "docker.io",
                      src_creds: Optional[str] = None, 
                      dest_creds: Optional[str] = None) -> Dict[str, bool]:
        """
        从文件中读取镜像列表并进行批量同步

        Args:
            image_list_file: 包含镜像列表的文件路径
            destination_registry: 目标仓库地址
            source_registry: 源仓库地址，默认为docker.io
            src_creds: 源仓库认证信息
            dest_creds: 目标仓库认证信息

        Returns:
            镜像同步结果字典 {镜像名称: 是否成功}
        """
        images = self.read_image_list(image_list_file)
        return self.sync_images(images, destination_registry, source_registry, src_creds, dest_creds)

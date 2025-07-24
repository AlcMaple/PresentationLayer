import os
import uuid
from typing import Optional
from fastapi import UploadFile
from datetime import datetime

from config.settings import settings


class FileUploadService:
    """文件上传服务"""

    def __init__(self):
        # 基础上传目录
        self.base_upload_dir = "static/uploads"
        # 图片上传目录
        self.image_upload_dir = os.path.join(self.base_upload_dir, "images")

        # 支持的图片格式
        self.allowed_image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
        }

        # 最大文件大小 (10MB)
        self.max_file_size = 10 * 1024 * 1024

        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保上传目录存在"""
        os.makedirs(self.image_upload_dir, exist_ok=True)

    def _generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        # 获取文件扩展名
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        # 生成唯一文件名：日期_UUID_原始名
        date_str = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8]
        base_name = os.path.splitext(original_filename)[0][:20]

        return f"{date_str}_{unique_id}_{base_name}{ext}"

    def _validate_image_file(self, file: UploadFile) -> tuple[bool, str]:
        """验证图片文件"""
        # 检查文件名
        if not file.filename:
            return False, "文件名不能为空"

        # 检查扩展名
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in self.allowed_image_extensions:
            return (
                False,
                f"不支持的图片格式，支持格式：{', '.join(self.allowed_image_extensions)}",
            )

        # 检查文件大小
        if file.size and file.size > self.max_file_size:
            return False, f"文件大小超过限制（{self.max_file_size // (1024*1024)}MB）"

        # 检查MIME类型
        if file.content_type and not file.content_type.startswith("image/"):
            return False, "文件类型必须是图片"

        return True, ""

    async def save_image(self, file: UploadFile) -> tuple[bool, str, Optional[str]]:
        """
        保存图片文件

        Args:
            file: 上传的文件对象

        Returns:
            (是否成功, 消息, 图片URL)
        """
        try:
            # 验证文件
            is_valid, error_msg = self._validate_image_file(file)
            if not is_valid:
                return False, error_msg, None

            # 生成文件名
            filename = self._generate_filename(file.filename)
            file_path = os.path.join(self.image_upload_dir, filename)

            # 保存文件
            content = await file.read()

            # 检查实际文件大小
            if len(content) > self.max_file_size:
                return (
                    False,
                    f"文件大小超过限制（{self.max_file_size // (1024*1024)}MB）",
                    None,
                )

            with open(file_path, "wb") as f:
                f.write(content)

            # 生成访问URL
            image_url = f"/static/uploads/images/{filename}"

            return True, "图片保存成功", image_url

        except Exception as e:
            return False, f"保存图片失败：{str(e)}", None

    # def delete_image(self, image_url: str) -> tuple[bool, str]:
    #     """
    #     删除图片文件

    #     Args:
    #         image_url: 图片URL

    #     Returns:
    #         (是否成功, 消息)
    #     """
    #     try:
    #         # 从URL提取文件名
    #         if not image_url.startswith("/static/uploads/images/"):
    #             return False, "无效的图片URL"

    #         filename = image_url.replace("/static/uploads/images/", "")
    #         file_path = os.path.join(self.image_upload_dir, filename)

    #         # 检查文件是否存在
    #         if not os.path.exists(file_path):
    #             return False, "图片文件不存在"

    #         # 删除文件
    #         os.remove(file_path)

    #         return True, "图片删除成功"

    #     except Exception as e:
    #         return False, f"删除图片失败：{str(e)}"

    def get_file_info(self, image_url: str) -> Optional[dict]:
        """
        获取文件信息

        Args:
            image_url: 图片URL

        Returns:
            文件信息
        """
        try:
            if not image_url.startswith("/static/uploads/images/"):
                return None

            filename = image_url.replace("/static/uploads/images/", "")
            file_path = os.path.join(self.image_upload_dir, filename)

            if not os.path.exists(file_path):
                return None

            stat = os.stat(file_path)

            return {
                "filename": filename,
                "size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "url": image_url,
            }

        except Exception:
            return None


def get_file_upload_service() -> FileUploadService:
    """获取文件上传服务实例"""
    return FileUploadService()

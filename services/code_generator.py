from sqlmodel import Session, text
from typing import Optional

from models.enums import CodePrefix
from exceptions import ValidationException, DuplicateException


class CodeGeneratorService:
    """编码生成服务"""

    def __init__(self, session: Session):
        self.session = session

    def generate_code(self, table_name: str) -> str:
        """
        生成编码

        Args:
            table_name: 表名

        Returns:
            生成的编码，格式：前缀_数字，如 BT_1
        """
        # 获取前缀
        prefix_enum = CodePrefix.__members__.get(table_name.upper())
        prefix = prefix_enum.value if prefix_enum else "UK"

        # 查询该表当前最大的编码序号
        max_sequence = self._get_max_sequence(table_name, prefix)
        new_sequence = max_sequence + 1

        # 格式化：前缀_数字
        return f"{prefix}_{new_sequence}"

    def _get_max_sequence(self, table_name: str, prefix: str) -> int:
        """
        获取指定表的最大序号

        Args:
            table_name: 表名
            prefix: 编码前缀

        Returns:
            最大序号，如果没有找到则返回0
        """
        try:
            sql = text(
                f"""
                SELECT code FROM {table_name}
                WHERE code LIKE :prefix_pattern
            """
            )
            result = self.session.execute(sql, {"prefix_pattern": f"{prefix}_%"})
            codes = [row[0] for row in result.fetchall()]
            max_seq = 0
            for code in codes:
                try:
                    number = int(code.split("_")[1])
                    max_seq = max(max_seq, number)
                except (IndexError, ValueError):
                    continue
            return max_seq
        except Exception as e:
            print(f"获取最大序号时出错: {e}")
            return 0

    def batch_generate_codes(self, table_name: str, count: int) -> list[str]:
        """
        批量生成编码

        Args:
            table_name: 表名
            count: 需要生成的数量

        Returns:
            生成的编码列表
        """
        prefix_enum = CodePrefix.__members__.get(table_name.upper())
        prefix = prefix_enum.value if prefix_enum else "UK"

        max_sequence = self._get_max_sequence(table_name, prefix)

        codes = []
        for i in range(1, count + 1):
            new_sequence = max_sequence + i
            codes.append(f"{prefix}_{new_sequence}")

        return codes

    def validate_code_format(self, code: str, table_name: str) -> bool:
        """
        验证编码格式是否正确

        Args:
            code: 待验证的编码
            table_name: 表名

        Returns:
            是否符合格式要求
        """
        if not code:
            return False

        prefix_enum = CodePrefix.__members__.get(table_name.upper())
        prefix = prefix_enum.value if prefix_enum else "UK"

        # 检查是否以前缀_开头
        if not code.startswith(f"{prefix}_"):
            return False

        # 提取数字部分
        number_part = code[len(prefix) + 1 :]
        if not number_part.isdigit():
            return False

        # 检查数字是否大于0
        if int(number_part) <= 0:
            return False

        return True

    def code_exists(self, table_name: str, code: str) -> bool:
        """
        检查编码是否已存在

        Args:
            table_name: 表名
            code: 待检查的编码

        Returns:
            是否存在
        """
        try:
            sql = text(f"SELECT 1 FROM {table_name} WHERE code = :code LIMIT 1")
            result = self.session.execute(sql, {"code": code})
            return result.fetchone() is not None
        except Exception:
            return False

    def assign_or_generate_code(
        self, table_name: str, user_code: Optional[str] = None
    ) -> str:
        """
        Args:
            table_name: 表名
            user_code: 用户自定义编码
        """
        if user_code:
            clean_code = user_code.strip()
            if self.code_exists(table_name, clean_code):
                raise DuplicateException(
                    resource=table_name, field="code", value=clean_code
                )
            return clean_code

        return self.generate_code(table_name)


# 工厂函数
def get_code_generator(session: Session) -> CodeGeneratorService:
    """获取编码生成器实例"""
    return CodeGeneratorService(session)

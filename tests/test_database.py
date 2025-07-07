import pytest
from sqlmodel import text

from config.database import engine, get_db


class TestDatabase:
    """数据库测试类"""

    def test_database_connection(self):
        """测试数据库连接"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test_value"))
                row = result.fetchone()
                assert row[0] == 1, "数据库查询结果不正确"
                print("数据库连接测试通过")
        except Exception as e:
            pytest.fail(f"数据库连接失败: {e}")

    def test_session_dependency(self):
        """测试数据库会话"""
        session_gen = get_db()
        session = next(session_gen)

        result = session.exec(text("SELECT VERSION() as version"))
        row = result.fetchone()
        assert row is not None, "会话查询失败"
        print(f"数据库版本: {row[0]}")

        # 清理会话
        try:
            next(session_gen)
        except StopIteration:
            pass  # 正常结束

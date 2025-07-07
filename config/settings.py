from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    """ """

    # 环境配置
    ENVIRONMENT: Literal["development", "production"] = "development"

    # 基础配置
    PROJECT_NAME: str = "桥梁健康监控系统"
    VERSION: str = "1.0.0"

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8002

    # 数据库配置
    MYSQL_SERVER: str = "localhost"
    MYSQL_USER: str = "username"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "database"
    MYSQL_PORT: int = 3306

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env" if os.getenv("ENVIRONMENT") != "production" else None
        env_file_encoding = "utf-8"
        case_sensitive = True  # 区分大小写


settings = Settings()

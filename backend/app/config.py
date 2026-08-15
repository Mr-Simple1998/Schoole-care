from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，可通过环境变量或 .env 文件覆盖"""
    app_name: str = "后台学习管理系统 API"
    database_url: str = "sqlite:///./tortoise.db"
    debug: bool = True
    # 微信小程序（留空则退化为本地开发模拟模式：code 直接作为 openid）
    wx_appid: str = ""
    wx_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
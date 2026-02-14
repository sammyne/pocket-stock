"""
搜索配置管理

处理搜索模块的配置加载和验证，使用 pydantic-settings 进行配置管理。
"""


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pocket_stock.search.exceptions import ConfigurationError


class SearchSettings(BaseSettings):
    """搜索配置类，基于 pydantic-settings 的 BaseSettings

    从环境变量加载配置，支持 .env 文件自动加载。
    """

    model_config = SettingsConfigDict(
        env_prefix="TAVILY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(description="Tavily API 密钥")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """验证 API key

        Args:
            v: API key 值

        Returns:
            验证后的 API key

        Raises:
            ValueError: 当 API key 为空或格式不正确时抛出
        """
        if not v or not v.strip():
            raise ValueError("API key 不能为空")
        return v.strip()

    def validate(self) -> bool:
        """验证配置是否有效

        Returns:
            如果配置有效返回 True

        Raises:
            ConfigurationError: 当配置无效时抛出
        """
        if not self.api_key:
            raise ConfigurationError("API key 不能为空")

        if len(self.api_key) < 10:
            raise ConfigurationError("API key 长度似乎不正确")

        return True

    def __repr__(self) -> str:
        """返回配置的字符串表示

        Returns:
            字符串表示，隐藏 API key 的敏感信息
        """
        masked_key = "***" if self.api_key else "None"
        return f"SearchSettings(api_key={masked_key})"


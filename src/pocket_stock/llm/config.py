"""配置管理模块。

提供 LLM 配置的加载和验证功能。
"""

from typing import ClassVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from .exceptions import ConfigurationError


class LLMConfig(BaseSettings):
    """LLM 配置类。

    从环境变量读取 LLM 相关的配置信息，并进行验证。

    Attributes:
        openai_model: OpenAI 兼容的模型名称。
        openai_api_base_url: OpenAI 兼容的 API 服务地址。
        openai_api_key: 访问 API 服务所需的密钥。

    Raises:
        ConfigurationError: 当缺少必需的配置项时抛出。
    """

    # 使用字段别名映射环境变量名
    openai_model: str = Field(
        ...,
        alias="OPENAI_MODEL",
        description="OpenAI 兼容的模型名称",
    )
    openai_api_base_url: str = Field(
        ...,
        alias="OPENAI_API_BASE_URL",
        description="OpenAI 兼容的 API 服务地址",
    )
    openai_api_key: str = Field(
        ...,
        alias="OPENAI_API_KEY",
        description="访问 API 服务所需的密钥",
    )

    # 环境变量文件配置
    model_config: ClassVar[dict] = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("openai_model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        """验证模型名称。

        Args:
            value: 模型名称。

        Returns:
            验证通过的模型名称。

        Raises:
            ConfigurationError: 当模型名称为空时抛出。
        """
        if not value or not value.strip():
            raise ConfigurationError("OPENAI_MODEL 不能为空")
        return value.strip()

    @field_validator("openai_api_base_url")
    @classmethod
    def validate_api_base_url(cls, value: str) -> str:
        """验证 API 基础 URL。

        Args:
            value: API 基础 URL。

        Returns:
            验证通过的 API 基础 URL。

        Raises:
            ConfigurationError: 当 API 基础 URL 为空时抛出。
        """
        if not value or not value.strip():
            raise ConfigurationError("OPENAI_API_BASE_URL 不能为空")
        return value.strip()

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        """验证 API 密钥。

        Args:
            value: API 密钥。

        Returns:
            验证通过的 API 密钥。

        Raises:
            ConfigurationError: 当 API 密钥为空时抛出。
        """
        if not value or not value.strip():
            raise ConfigurationError("OPENAI_API_KEY 不能为空")
        return value.strip()

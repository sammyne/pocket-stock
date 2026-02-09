"""模块配置类。"""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """数据提供者配置类。

    该类用于配置异步 HTTP 请求的超时时间。

    Attributes:
        timeout: 异步请求超时时间（秒），默认为 10 秒

    Examples:
        >>> config = ProviderConfig(timeout=15)
        >>> config.timeout
        15
    """

    timeout: float = Field(default=10.0, gt=0, description="异步请求超时时间（秒）")

    @classmethod
    def from_dict(cls, config_dict: Mapping[str, Any]) -> "ProviderConfig":
        """从字典创建配置对象。

        Args:
            config_dict: 配置字典，键为参数名，值为参数值

        Returns:
            配置对象实例

        Examples:
            >>> config = ProviderConfig.from_dict({"timeout": 15})
        """
        return cls(**{k: v for k, v in config_dict.items() if k in cls.model_fields})

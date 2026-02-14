"""搜索配置管理

处理搜索模块的配置加载和验证，使用 pydantic-settings 进行配置管理。
"""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


@dataclass
class SearchUserConfig:
    """用户搜索配置数据类

    管理用户自定义的搜索选项配置，持久化存储到本地文件。
    """

    max_results: int = 5
    search_depth: str = "basic"
    chunks_per_source: int = 3
    topic: str = "general"
    include_answer: bool = False
    include_answer_level: str | None = None
    country: str = "china"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            配置字典
        """
        return {
            "max_results": self.max_results,
            "search_depth": self.search_depth,
            "chunks_per_source": self.chunks_per_source,
            "topic": self.topic,
            "include_answer": self.include_answer,
            "include_answer_level": self.include_answer_level,
            "country": self.country,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchUserConfig":
        """从字典创建实例

        Args:
            data: 配置字典

        Returns:
            SearchUserConfig 实例
        """
        return cls(
            max_results=data.get("max_results", 5),
            search_depth=data.get("search_depth", "basic"),
            chunks_per_source=data.get("chunks_per_source", 3),
            topic=data.get("topic", "general"),
            include_answer=data.get("include_answer", False),
            include_answer_level=data.get("include_answer_level"),
            country=data.get("country", "china"),
        )

    def validate(self) -> tuple[bool, str | None]:
        """验证配置有效性

        Returns:
            元组 (是否有效, 错误消息)
        """
        # 验证 max_results
        if not isinstance(self.max_results, int) or self.max_results < 0 or self.max_results > 20:
            return False, "max_results 必须是 0 到 20 之间的整数"

        # 验证 search_depth
        valid_depths = {"basic", "advanced", "fast", "ultra-fast"}
        if self.search_depth not in valid_depths:
            return False, f"search_depth 必须是以下之一: {', '.join(valid_depths)}"

        # 验证 chunks_per_source
        if not isinstance(self.chunks_per_source, int) or self.chunks_per_source < 1 or self.chunks_per_source > 3:
            return False, "chunks_per_source 必须是 1 到 3 之间的整数"

        # 验证 topic
        valid_topics = {"general", "news", "finance"}
        if self.topic not in valid_topics:
            return False, f"topic 必须是以下之一: {', '.join(valid_topics)}"

        # 验证 include_answer_level
        if self.include_answer and self.include_answer_level not in {"basic", "advanced"}:
            return False, "include_answer_level 必须是 'basic' 或 'advanced'"

        # 验证 country
        if self.topic == "general" and not self.country or not self.country.strip():
            return False, "country 不能为空"

        return True, None


class SearchConfigManager:
    """搜索配置管理器

    负责用户搜索配置的持久化存储、加载和管理。
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录，如果为 None 则使用默认目录
        """
        if config_dir is None:
            # 使用 .streamlit 目录作为配置目录
            config_dir = Path(".streamlit")

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "search.yaml"

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> SearchUserConfig:
        """加载用户配置

        如果配置文件不存在或损坏，返回默认配置。

        Returns:
            SearchUserConfig 实例
        """
        if not self.config_file.exists():
            return SearchUserConfig()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return SearchUserConfig.from_dict(data if data else {})
        except (yaml.YAMLError, IOError) as e:
            # 配置文件损坏，返回默认配置
            return SearchUserConfig()

    def save(self, config: SearchUserConfig) -> bool:
        """保存用户配置

        Args:
            config: 要保存的配置

        Returns:
            是否保存成功
        """
        try:
            # 验证配置
            is_valid, error_msg = config.validate()
            if not is_valid:
                raise ConfigurationError(error_msg)

            # 写入配置文件
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    config.to_dict(),
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=False,
                )
            return True
        except (IOError, ConfigurationError) as e:
            return False

    def reset(self) -> bool:
        """重置为默认配置

        Returns:
            是否重置成功
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            return True
        except IOError:
            return False

    def get_config_file_path(self) -> Path:
        """获取配置文件路径

        Returns:
            配置文件路径
        """
        return self.config_file

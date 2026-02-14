"""搜索配置单元测试。"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml

from pocket_stock.search.config import (
    SearchConfigManager,
    SearchSettings,
    SearchUserConfig,
)
from pocket_stock.search.exceptions import ConfigurationError


class TestSearchUserConfig:
    """SearchUserConfig 测试类。"""

    def test_default_config(self) -> None:
        """测试默认配置。"""
        config = SearchUserConfig()
        assert config.max_results == 5
        assert config.search_depth == "basic"
        assert config.chunks_per_source == 3
        assert config.topic == "general"
        assert config.include_answer is False
        assert config.include_answer_level is None
        assert config.country == "china"

    def test_custom_config(self) -> None:
        """测试自定义配置。"""
        config = SearchUserConfig(
            max_results=10,
            search_depth="advanced",
            chunks_per_source=2,
            topic="news",
            include_answer=True,
            include_answer_level="advanced",
            country="us",
        )
        assert config.max_results == 10
        assert config.search_depth == "advanced"
        assert config.chunks_per_source == 2
        assert config.topic == "news"
        assert config.include_answer is True
        assert config.include_answer_level == "advanced"
        assert config.country == "us"

    def test_to_dict(self) -> None:
        """测试转换为字典。"""
        config = SearchUserConfig(max_results=10)
        data = config.to_dict()
        assert isinstance(data, dict)
        assert data["max_results"] == 10
        assert data["search_depth"] == "basic"

    def test_from_dict(self) -> None:
        """测试从字典创建实例。"""
        data = {
            "max_results": 10,
            "search_depth": "advanced",
            "chunks_per_source": 2,
            "topic": "news",
            "include_answer": True,
            "include_answer_level": "advanced",
            "country": "us",
        }
        config = SearchUserConfig.from_dict(data)
        assert config.max_results == 10
        assert config.search_depth == "advanced"
        assert config.chunks_per_source == 2
        assert config.topic == "news"
        assert config.include_answer is True
        assert config.include_answer_level == "advanced"
        assert config.country == "us"

    def test_from_dict_with_defaults(self) -> None:
        """测试从字典创建实例时使用默认值。"""
        data = {"max_results": 10}
        config = SearchUserConfig.from_dict(data)
        assert config.max_results == 10
        assert config.search_depth == "basic"
        assert config.chunks_per_source == 3

    def test_validate_success(self) -> None:
        """测试配置验证成功。"""
        config = SearchUserConfig()
        is_valid, error_msg = config.validate()
        assert is_valid is True
        assert error_msg is None

    def test_validate_invalid_max_results(self) -> None:
        """测试无效的 max_results。"""
        config = SearchUserConfig(max_results=25)
        is_valid, error_msg = config.validate()
        assert is_valid is False
        assert "max_results" in error_msg

    def test_validate_invalid_search_depth(self) -> None:
        """测试无效的 search_depth。"""
        config = SearchUserConfig(search_depth="invalid")
        is_valid, error_msg = config.validate()
        assert is_valid is False
        assert "search_depth" in error_msg

    def test_validate_invalid_chunks_per_source(self) -> None:
        """测试无效的 chunks_per_source。"""
        config = SearchUserConfig(chunks_per_source=5)
        is_valid, error_msg = config.validate()
        assert is_valid is False
        assert "chunks_per_source" in error_msg

    def test_validate_invalid_topic(self) -> None:
        """测试无效的 topic。"""
        config = SearchUserConfig(topic="invalid")
        is_valid, error_msg = config.validate()
        assert is_valid is False
        assert "topic" in error_msg

    def test_validate_invalid_include_answer_level(self) -> None:
        """测试无效的 include_answer_level。"""
        config = SearchUserConfig(include_answer=True, include_answer_level="invalid")
        is_valid, error_msg = config.validate()
        assert is_valid is False
        assert "include_answer_level" in error_msg

    def test_validate_empty_country_with_general_topic(self) -> None:
        """测试 general topic 时 country 为空。"""
        config = SearchUserConfig(topic="general", country="")
        is_valid, error_msg = config.validate()
        assert is_valid is False
        assert "country" in error_msg


class TestSearchConfigManager:
    """SearchConfigManager 测试类。"""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """创建临时配置目录。"""
        config_dir = tmp_path / ".streamlit"
        return config_dir

    @pytest.fixture
    def config_manager(self, temp_config_dir: Path) -> SearchConfigManager:
        """创建配置管理器实例。"""
        return SearchConfigManager(temp_config_dir)

    def test_init_default_dir(self) -> None:
        """测试使用默认目录初始化。"""
        manager = SearchConfigManager()
        assert manager.config_dir == Path(".streamlit")
        assert manager.config_file.name == "search.yaml"

    def test_init_custom_dir(self, temp_config_dir: Path) -> None:
        """测试使用自定义目录初始化。"""
        manager = SearchConfigManager(temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.config_file.name == "search.yaml"

    def test_load_file_not_exists(self, config_manager: SearchConfigManager) -> None:
        """测试配置文件不存在时加载。"""
        config = config_manager.load()
        assert isinstance(config, SearchUserConfig)
        assert config.max_results == 5  # 默认值

    def test_load_and_save(self, config_manager: SearchConfigManager) -> None:
        """测试保存和加载配置。"""
        original_config = SearchUserConfig(
            max_results=10,
            search_depth="advanced",
            chunks_per_source=2,
            topic="news",
            include_answer=True,
            include_answer_level="advanced",
            country="us",
        )

        # 保存配置
        result = config_manager.save(original_config)
        assert result is True

        # 验证文件存在
        assert config_manager.config_file.exists()

        # 验证文件内容是 YAML 格式
        with open(config_manager.config_file, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)
            assert loaded_data["max_results"] == 10
            assert loaded_data["search_depth"] == "advanced"

        # 加载配置
        loaded_config = config_manager.load()
        assert loaded_config.max_results == original_config.max_results
        assert loaded_config.search_depth == original_config.search_depth
        assert loaded_config.chunks_per_source == original_config.chunks_per_source
        assert loaded_config.topic == original_config.topic
        assert loaded_config.include_answer == original_config.include_answer
        assert loaded_config.include_answer_level == original_config.include_answer_level
        assert loaded_config.country == original_config.country

    def test_save_invalid_config(self, config_manager: SearchConfigManager) -> None:
        """测试保存无效配置。"""
        invalid_config = SearchUserConfig(max_results=25)
        result = config_manager.save(invalid_config)
        assert result is False

    def test_reset(self, config_manager: SearchConfigManager) -> None:
        """测试重置配置。"""
        # 保存配置
        config = SearchUserConfig(max_results=10)
        config_manager.save(config)

        # 验证文件存在
        assert config_manager.config_file.exists()

        # 重置配置
        result = config_manager.reset()
        assert result is True

        # 验证文件已删除
        assert not config_manager.config_file.exists()

    def test_get_config_file_path(self, config_manager: SearchConfigManager) -> None:
        """测试获取配置文件路径。"""
        path = config_manager.get_config_file_path()
        assert path == config_manager.config_file

    def test_load_corrupted_yaml(self, config_manager: SearchConfigManager) -> None:
        """测试加载损坏的 YAML 文件。"""
        # 创建损坏的 YAML 文件
        config_manager.config_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        # 加载应返回默认配置
        config = config_manager.load()
        assert config.max_results == 5  # 默认值

    def test_yaml_format_unicode_support(self, config_manager: SearchConfigManager) -> None:
        """测试 YAML 格式的 Unicode 支持。"""
        config = SearchUserConfig(topic="general", country="china")
        config_manager.save(config)

        # 读取文件内容，验证 YAML 格式
        with open(config_manager.config_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "china" in content
            assert "general" in content

        # 验证可以正确加载
        loaded_config = config_manager.load()
        assert loaded_config.country == "china"
        assert loaded_config.topic == "general"


class TestSearchSettings:
    """SearchSettings 测试类。"""

    def test_validate_api_key(self) -> None:
        """测试 API key 验证。"""
        with pytest.raises(ValueError) as exc_info:
            SearchSettings(api_key="  ")
        assert "不能为空" in str(exc_info.value)

    def test_validate_success(self) -> None:
        """测试配置验证成功。"""
        settings = SearchSettings(api_key="test_api_key_123456789")
        assert settings.validate() is True

    def test_validate_empty_api_key(self) -> None:
        """测试空的 API key。"""
        with pytest.raises(ValueError) as exc_info:
            SearchSettings(api_key="")
        assert "不能为空" in str(exc_info.value)

    def test_validate_short_api_key(self) -> None:
        """测试过短的 API key。"""
        settings = SearchSettings(api_key="short")
        with pytest.raises(ConfigurationError) as exc_info:
            settings.validate()
        assert "长度" in str(exc_info.value)

    def test_repr_masks_api_key(self) -> None:
        """测试 repr 方法隐藏 API key。"""
        settings = SearchSettings(api_key="test_api_key_123456789")
        repr_str = repr(settings)
        assert "***" in repr_str
        assert "test_api_key_123456789" not in repr_str

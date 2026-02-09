"""配置类单元测试。"""

import pytest
from pydantic import ValidationError

from pocket_stock.data_provider.config import ProviderConfig


class TestProviderConfig:
    """ProviderConfig 测试类。"""

    def test_default_config(self) -> None:
        """测试默认配置。"""
        config = ProviderConfig()
        assert config.timeout == 10.0

    def test_custom_config(self) -> None:
        """测试自定义配置。"""
        config = ProviderConfig(timeout=15.0)
        assert config.timeout == 15.0

    def test_invalid_timeout(self) -> None:
        """测试无效的超时时间。"""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(timeout=-1.0)
        assert "timeout" in str(exc_info.value).lower()

    def test_zero_timeout(self) -> None:
        """测试零超时时间。"""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(timeout=0.0)
        assert "timeout" in str(exc_info.value).lower()

    def test_from_dict(self) -> None:
        """测试从字典创建配置。"""
        config_dict = {"timeout": 15.0}
        config = ProviderConfig.from_dict(config_dict)
        assert config.timeout == 15.0

    def test_from_dict_with_extra_fields(self) -> None:
        """测试从字典创建配置时忽略额外字段。"""
        config_dict = {
            "timeout": 15.0,
            "extra_field": "ignored",
        }
        config = ProviderConfig.from_dict(config_dict)
        assert config.timeout == 15.0
        assert not hasattr(config, "extra_field")

    def test_model_serialization(self) -> None:
        """测试模型序列化。"""
        config = ProviderConfig(timeout=15.0)

        # 测试 model_dump
        data_dict = config.model_dump()
        assert data_dict["timeout"] == 15.0

        # 测试 model_dump_json
        json_str = config.model_dump_json()
        assert "15.0" in json_str

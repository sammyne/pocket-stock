"""LLM 配置类单元测试。"""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from pocket_stock.llm.config import LLMConfig
from pocket_stock.llm.exceptions import ConfigurationError


class TestLLMConfig:
    """LLMConfig 测试类。"""

    def test_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试从环境变量加载配置。"""
        # 设置环境变量
        monkeypatch.setenv("OPENAI_MODEL", "qwen-max")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")

        config = LLMConfig()
        assert config.openai_model == "qwen-max"
        assert config.openai_api_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert config.openai_api_key == "test-api-key"

    def test_config_from_env_file(self) -> None:
        """测试从 .env 文件加载配置。"""
        # 创建临时 .env 文件
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """OPENAI_MODEL=gpt-4
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-test-key
"""
            )

            # 切换工作目录到临时目录
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config = LLMConfig()
                assert config.openai_model == "gpt-4"
                assert config.openai_api_base_url == "https://api.openai.com/v1"
                assert config.openai_api_key == "sk-test-key"
            finally:
                os.chdir(original_cwd)

    def test_config_missing_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试缺少模型名称时抛出异常。"""
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        # 不设置 OPENAI_MODEL

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig()
        assert "OPENAI_MODEL" in str(exc_info.value)

    def test_config_missing_api_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试缺少 API 基础 URL 时抛出异常。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        # 不设置 OPENAI_API_BASE_URL

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig()
        assert "OPENAI_API_BASE_URL" in str(exc_info.value)

    def test_config_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试缺少 API 密钥时抛出异常。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        # 不设置 OPENAI_API_KEY

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig()
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_config_empty_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试模型名称为空时抛出异常。"""
        monkeypatch.setenv("OPENAI_MODEL", "   ")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        with pytest.raises(ConfigurationError) as exc_info:
            LLMConfig()
        assert "OPENAI_MODEL 不能为空" in str(exc_info.value)

    def test_config_empty_api_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 API 基础 URL 为空时抛出异常。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "   ")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        with pytest.raises(ConfigurationError) as exc_info:
            LLMConfig()
        assert "OPENAI_API_BASE_URL 不能为空" in str(exc_info.value)

    def test_config_empty_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 API 密钥为空时抛出异常。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "   ")

        with pytest.raises(ConfigurationError) as exc_info:
            LLMConfig()
        assert "OPENAI_API_KEY 不能为空" in str(exc_info.value)

    def test_config_whitespace_trimming(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试配置值自动去除首尾空格。"""
        monkeypatch.setenv("OPENAI_MODEL", "  gpt-4  ")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "  https://api.openai.com/v1  ")
        monkeypatch.setenv("OPENAI_API_KEY", "  sk-test-key  ")

        config = LLMConfig()
        assert config.openai_model == "gpt-4"
        assert config.openai_api_base_url == "https://api.openai.com/v1"
        assert config.openai_api_key == "sk-test-key"

    def test_config_serialization(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试配置序列化。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        config = LLMConfig()

        # 测试 model_dump
        data_dict = config.model_dump()
        assert data_dict["openai_model"] == "gpt-4"
        assert data_dict["openai_api_base_url"] == "https://api.openai.com/v1"
        assert data_dict["openai_api_key"] == "sk-test-key"

        # 测试 model_dump_json
        json_str = config.model_dump_json()
        assert "gpt-4" in json_str
        assert "https://api.openai.com/v1" in json_str

    def test_config_extra_fields_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试额外字段被忽略。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("OPENAI_EXTRA_FIELD", "should_be_ignored")

        config = LLMConfig()
        assert not hasattr(config, "openai_extra_field")

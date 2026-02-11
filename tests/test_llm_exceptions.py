"""LLM 模块异常类单元测试。"""

from pocket_stock.llm.exceptions import (
    ConfigurationError,
    LLMAnalysisError,
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMResponseParseError,
    LLMServiceError,
    NetworkConnectionError,
)


class TestLLMAnalysisError:
    """LLMAnalysisError 测试类。"""

    def test_base_exception(self) -> None:
        """测试基础异常类。"""
        exc = LLMAnalysisError("测试错误")
        assert str(exc) == "测试错误"


class TestConfigurationError:
    """ConfigurationError 测试类。"""

    def test_configuration_error(self) -> None:
        """测试配置错误异常。"""
        exc = ConfigurationError("OPENAI_API_KEY 不能为空")
        assert "OPENAI_API_KEY 不能为空" in str(exc)
        assert isinstance(exc, LLMAnalysisError)


class TestLLMApiTimeoutError:
    """LLMApiTimeoutError 测试类。"""

    def test_api_timeout_error(self) -> None:
        """测试 API 超时错误异常。"""
        exc = LLMApiTimeoutError("API 调用超时（30秒）")
        assert "API 调用超时" in str(exc)
        assert isinstance(exc, LLMAnalysisError)


class TestLLMAuthenticationError:
    """LLMAuthenticationError 测试类。"""

    def test_authentication_error(self) -> None:
        """测试认证错误异常。"""
        exc = LLMAuthenticationError("API 密钥无效")
        assert "API 密钥无效" in str(exc)
        assert isinstance(exc, LLMAnalysisError)


class TestLLMServiceError:
    """LLMServiceError 测试类。"""

    def test_service_error(self) -> None:
        """测试服务错误异常。"""
        exc = LLMServiceError("服务返回 500 错误")
        assert "500 错误" in str(exc)
        assert isinstance(exc, LLMAnalysisError)


class TestNetworkConnectionError:
    """NetworkConnectionError 测试类。"""

    def test_network_connection_error(self) -> None:
        """测试网络连接错误异常。"""
        exc = NetworkConnectionError("无法连接到 LLM 服务")
        assert "无法连接到 LLM 服务" in str(exc)
        assert isinstance(exc, LLMAnalysisError)


class TestLLMResponseParseError:
    """LLMResponseParseError 测试类。"""

    def test_response_parse_error(self) -> None:
        """测试响应解析错误异常。"""
        exc = LLMResponseParseError("无法解析 LLM 返回的 JSON 响应")
        assert "无法解析 LLM 返回的 JSON 响应" in str(exc)
        assert isinstance(exc, LLMAnalysisError)

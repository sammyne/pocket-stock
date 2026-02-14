"""异常类单元测试。"""


from pocket_stock.data_provider.exceptions import (
    DataParseError,
    DataProviderError,
    DataValidationError,
    InvalidStockCodeError,
    NetworkError,
    ProviderServiceError,
)


class TestDataProviderError:
    """DataProviderError 测试类。"""

    def test_base_exception(self) -> None:
        """测试基础异常类。"""
        exc = DataProviderError("测试错误")
        assert exc.message == "测试错误"
        assert str(exc) == "测试错误"


class TestInvalidStockCodeError:
    """InvalidStockCodeError 测试类。"""

    def test_invalid_stock_code_exception(self) -> None:
        """测试无效股票代码异常。"""
        exc = InvalidStockCodeError("股票代码不能为空")
        assert "股票代码不能为空" in str(exc)


class TestNetworkError:
    """NetworkError 测试类。"""

    def test_network_error_exception(self) -> None:
        """测试网络错误异常。"""
        exc = NetworkError("sh600000", "连接超时")
        assert exc.stock_code == "sh600000"
        assert exc.reason == "连接超时"
        assert "sh600000" in str(exc)
        assert "连接超时" in str(exc)


class TestProviderServiceError:
    """ProviderServiceError 测试类。"""

    def test_provider_service_error_exception(self) -> None:
        """测试数据提供者服务错误异常。"""
        exc = ProviderServiceError("sh600000", 404, "资源未找到")
        assert exc.stock_code == "sh600000"
        assert exc.status_code == 404
        assert exc.reason == "资源未找到"
        assert "sh600000" in str(exc)
        assert "404" in str(exc)
        assert "资源未找到" in str(exc)


class TestDataParseError:
    """DataParseError 测试类。"""

    def test_data_parse_exception(self) -> None:
        """测试数据解析错误异常。"""
        exc = DataParseError("sh600000", "JSON 格式错误")
        assert exc.stock_code == "sh600000"
        assert exc.detail == "JSON 格式错误"
        assert "sh600000" in str(exc)
        assert "JSON 格式错误" in str(exc)


class TestDataValidationError:
    """DataValidationError 测试类。"""

    def test_data_validation_exception(self) -> None:
        """测试数据验证错误异常。"""
        exc = DataValidationError("当前价格不能为负数")
        assert exc.message == "当前价格不能为负数"
        assert "当前价格不能为负数" in str(exc)

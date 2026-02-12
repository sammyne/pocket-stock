"""BaseStockDataProvider 抽象基类单元测试。"""

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import InvalidStockCodeException
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.provider import BaseStockDataProvider


class ConcreteStockDataProvider(BaseStockDataProvider):
    """用于测试 BaseStockDataProvider 的具体实现。"""

    def __init__(self, config: ProviderConfig, session: aiohttp.ClientSession | None = None) -> None:
        super().__init__(config, session)
        self._mock_quote = None

    def set_mock_quote(self, quote: StockQuote) -> None:
        """设置模拟的股票行情数据。"""
        self._mock_quote = quote

    async def _get(self, stock_code: str) -> StockQuote:
        """模拟获取股票行情数据。"""
        if self.session is None:
            raise RuntimeError("会话未初始化，请使用 async with 语句或手动设置 session")
        if self._mock_quote is None:
            return StockQuote(
                stock_code=stock_code,
                name="测试股票",
                current_price=10.0,
                change=0.0,
                change_percent=0.0,
            )
        return self._mock_quote


@pytest.mark.asyncio
class TestBaseStockDataProvider:
    """BaseStockDataProvider 异步测试类。"""

    @pytest.fixture
    def config(self) -> ProviderConfig:
        """创建配置对象。"""
        return ProviderConfig(timeout=10.0)

    @pytest.fixture
    def provider(self, config: ProviderConfig) -> ConcreteStockDataProvider:
        """创建提供者实例。"""
        return ConcreteStockDataProvider(config)

    async def test_abstract_class_cannot_be_instantiated(self, config: ProviderConfig) -> None:
        """测试抽象类无法直接实例化。"""
        with pytest.raises(TypeError):
            BaseStockDataProvider(config)  # type: ignore[abstract]

    async def test_validate_stock_code_valid(self, provider: ConcreteStockDataProvider) -> None:
        """测试有效的股票代码验证。"""
        # 不应该抛出异常
        provider._validate_stock_code("sh600000")
        provider._validate_stock_code("sz000001")

    async def test_validate_stock_code_invalid_length(self, provider: ConcreteStockDataProvider) -> None:
        """测试无效长度的股票代码验证。"""
        with pytest.raises(InvalidStockCodeException, match="应为8位字符"):
            provider._validate_stock_code("sh6000")

    async def test_validate_stock_code_invalid_prefix(self, provider: ConcreteStockDataProvider) -> None:
        """测试无效前缀的股票代码验证。"""
        with pytest.raises(InvalidStockCodeException, match='应以 "sh" 或 "sz" 开头'):
            provider._validate_stock_code("bj600000")

    async def test_validate_stock_code_invalid_suffix(self, provider: ConcreteStockDataProvider) -> None:
        """测试无效后缀的股票代码验证。"""
        with pytest.raises(InvalidStockCodeException, match="后6位应为数字"):
            provider._validate_stock_code("sh00a000")

    async def test_validate_stock_code_empty(self, provider: ConcreteStockDataProvider) -> None:
        """测试空股票代码验证。"""
        with pytest.raises(InvalidStockCodeException, match="应为8位字符"):
            provider._validate_stock_code("")

    async def test_context_manager_creates_session(self, config: ProviderConfig) -> None:
        """测试异步上下文管理器创建会话。"""
        provider = ConcreteStockDataProvider(config)
        assert provider.session is None

        async with provider:
            assert provider.session is not None
            assert provider._owned_session is True

    async def test_context_manager_closes_session(self, config: ProviderConfig) -> None:
        """测试异步上下文管理器关闭会话。"""
        provider = ConcreteStockDataProvider(config)

        async with provider:
            session = provider.session
            assert session is not None

        # 退出后应该关闭会话
        assert session.closed is True

    async def test_custom_session_not_closed(self, config: ProviderConfig) -> None:
        """测试自定义会话不会被关闭。"""
        custom_session = aiohttp.ClientSession()
        provider = ConcreteStockDataProvider(config, session=custom_session)

        assert provider._owned_session is False

        async with provider:
            assert provider.session is custom_session

        # 自定义会话不应该被关闭
        assert custom_session.closed is False

        await custom_session.close()

    async def test_get_valid_stock(self, provider: ConcreteStockDataProvider) -> None:
        """测试获取有效股票数据。"""
        async with provider:
            quote = await provider.get("sh600000")

            assert isinstance(quote, StockQuote)
            assert quote.stock_code == "sh600000"
            assert quote.name == "测试股票"

    async def test_get_without_session_raises_error(self, provider: ConcreteStockDataProvider) -> None:
        """测试未初始化会话时调用 _get 抛出错误。"""
        # 不使用 async with，让 _get 抛出 RuntimeError
        with pytest.raises(RuntimeError, match="会话未初始化"):
            await provider._get("sh600000")

    async def test_close_method(self, config: ProviderConfig) -> None:
        """测试 close 方法。"""
        provider = ConcreteStockDataProvider(config)

        async with provider:
            session = provider.session
            assert session is not None

        # 调用 close 应该已经关闭了会话
        assert session.closed is True

    async def test_get_logs_request_and_response(
        self, provider: ConcreteStockDataProvider, caplog: pytest.LogCaptureFixture
    ) -> None:
        """测试 get 方法记录请求和响应日志。"""
        with patch("pocket_stock.data_provider.provider.log_request", new_callable=AsyncMock) as mock_log_request:
            with patch("pocket_stock.data_provider.provider.log_response", new_callable=AsyncMock) as mock_log_response:
                async with provider:
                    await provider.get("sh600000")

                    mock_log_request.assert_called_once_with("sh600000", timeout=10.0)
                    mock_log_response.assert_called_once()

    async def test_get_logs_error(
        self, provider: ConcreteStockDataProvider, caplog: pytest.LogCaptureFixture
    ) -> None:
        """测试 get 方法记录错误日志。"""
        with patch("pocket_stock.data_provider.provider.log_error", new_callable=AsyncMock) as mock_log_error:
            with patch.object(provider, "_get", side_effect=Exception("Mock error")):
                async with provider:
                    try:
                        await provider.get("sh600000")
                    except Exception:
                        pass

                    mock_log_error.assert_called_once()

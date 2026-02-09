"""数据提供者异步单元测试。"""

import aiohttp
import pytest
from pytest_mock import MockerFixture

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    InvalidStockCodeException,
    NetworkErrorException,
    ProviderServiceErrorException,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.provider import StockDataProvider


@pytest.mark.asyncio
class TestStockDataProvider:
    """StockDataProvider 异步测试类。"""

    @pytest.fixture
    def config(self) -> ProviderConfig:
        """创建配置实例。"""
        return ProviderConfig(timeout=10.0)

    @pytest.fixture
    async def mock_session(self, mocker: MockerFixture) -> aiohttp.ClientSession:
        """创建模拟的 HTTP 会话。"""
        session = mocker.MagicMock(spec=aiohttp.ClientSession)
        return session

    async def test_get_stock_quote_success(self, config: ProviderConfig, mock_session: aiohttp.ClientSession, mocker: MockerFixture) -> None:
        """测试成功获取股票行情。"""
        # 模拟响应对象
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.text = mocker.AsyncMock(return_value='{"sh600000": {"name": "浦发银行", "price": 10.25}}')
        mock_response.__aenter__ = mocker.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mocker.AsyncMock(return_value=None)

        # 模拟会话 get 方法
        mock_session.get = mocker.MagicMock(return_value=mock_response)

        # 创建提供者并获取数据
        provider = StockDataProvider(config, session=mock_session)
        quote = await provider.get_stock_quote("sh600000")

        assert isinstance(quote, StockQuote)
        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25

    async def test_get_stock_quote_invalid_code(self, config: ProviderConfig, mock_session: aiohttp.ClientSession) -> None:
        """测试无效股票代码。"""
        provider = StockDataProvider(config, session=mock_session)

        with pytest.raises(InvalidStockCodeException, match="无效的股票代码格式"):
            await provider.get_stock_quote("invalid")

    async def test_get_stock_quote_http_error(self, config: ProviderConfig, mock_session: aiohttp.ClientSession, mocker: MockerFixture) -> None:
        """测试 HTTP 错误状态码。"""
        # 模拟响应对象
        mock_response = mocker.MagicMock()
        mock_response.status = 404
        mock_response.__aenter__ = mocker.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mocker.AsyncMock(return_value=None)

        # 模拟会话 get 方法
        mock_session.get = mocker.MagicMock(return_value=mock_response)

        # 创建提供者并获取数据
        provider = StockDataProvider(config, session=mock_session)

        with pytest.raises(ProviderServiceErrorException, match="HTTP 状态码: 404"):
            await provider.get_stock_quote("sh600000")

    async def test_get_stock_quote_empty_response(self, config: ProviderConfig, mock_session: aiohttp.ClientSession, mocker: MockerFixture) -> None:
        """测试空响应。"""
        # 模拟响应对象
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.text = mocker.AsyncMock(return_value="")
        mock_response.__aenter__ = mocker.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mocker.AsyncMock(return_value=None)

        # 模拟会话 get 方法
        mock_session.get = mocker.MagicMock(return_value=mock_response)

        # 创建提供者并获取数据
        provider = StockDataProvider(config, session=mock_session)

        with pytest.raises(NetworkErrorException, match="数据提供者返回空响应"):
            await provider.get_stock_quote("sh600000")

    async def test_get_stock_quote_timeout(self, config: ProviderConfig, mock_session: aiohttp.ClientSession, mocker: MockerFixture) -> None:
        """测试请求超时。"""
        # 模拟会话 get 方法抛出超时异常
        mock_session.get = mocker.MagicMock(side_effect=aiohttp.ServerTimeoutError("请求超时"))

        # 创建提供者并获取数据
        provider = StockDataProvider(config, session=mock_session)

        # 注意：这里可能需要调整具体的异常类型
        with pytest.raises(NetworkErrorException):
            await provider.get_stock_quote("sh600000")

    async def test_get_stock_quote_network_error(self, config: ProviderConfig, mock_session: aiohttp.ClientSession, mocker: MockerFixture) -> None:
        """测试网络连接错误。"""
        # 模拟会话 get 方法抛出连接错误
        mock_session.get = mocker.MagicMock(side_effect=aiohttp.ClientError("连接失败"))

        # 创建提供者并获取数据
        provider = StockDataProvider(config, session=mock_session)

        with pytest.raises(NetworkErrorException, match="网络请求失败"):
            await provider.get_stock_quote("sh600000")

    async def test_context_manager(self, config: ProviderConfig, mocker: MockerFixture) -> None:
        """测试异步上下文管理器。"""
        # 模拟 ClientSession
        mock_session = mocker.MagicMock(spec=aiohttp.ClientSession)
        mock_session.close = mocker.AsyncMock()

        # 模拟响应对象
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.text = mocker.AsyncMock(return_value='{"sh600000": {"name": "浦发银行", "price": 10.25}}')
        mock_response.__aenter__ = mocker.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mocker.AsyncMock(return_value=None)

        # 模拟会话 get 方法
        mock_session.get = mocker.MagicMock(return_value=mock_response)

        # 模拟 ClientSession 创建
        mock_client_session_class = mocker.patch("aiohttp.ClientSession")
        mock_client_session_class.return_value = mock_session

        # 使用上下文管理器
        async with StockDataProvider(config) as provider:
            quote = await provider.get_stock_quote("sh600000")
            assert quote.name == "浦发银行"

        # 验证会话被关闭
        mock_session.close.assert_called_once()

    async def test_custom_session(self, config: ProviderConfig, mock_session: aiohttp.ClientSession, mocker: MockerFixture) -> None:
        """测试使用自定义会话。"""
        # 模拟响应对象
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.text = mocker.AsyncMock(return_value='{"sh600000": {"name": "浦发银行", "price": 10.25}}')
        mock_response.__aenter__ = mocker.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mocker.AsyncMock(return_value=None)

        # 模拟会话 get 方法
        mock_session.get = mocker.MagicMock(return_value=mock_response)

        # 创建提供者并使用自定义会话
        provider = StockDataProvider(config, session=mock_session)
        quote = await provider.get_stock_quote("sh600000")

        assert quote.name == "浦发银行"

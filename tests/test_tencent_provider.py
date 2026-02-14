"""TencentStockDataProvider 单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    InvalidStockCodeError,
    NetworkError,
    ProviderServiceError,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.tencent.provider import TencentStockDataProvider


@pytest.mark.asyncio
class TestTencentStockDataProvider:
    """TencentStockDataProvider 异步测试类。"""

    @pytest.fixture
    def config(self) -> ProviderConfig:
        """创建配置对象。"""
        return ProviderConfig(timeout=10.0)

    @pytest.fixture
    def provider(self, config: ProviderConfig) -> TencentStockDataProvider:
        """创建提供者实例。"""
        return TencentStockDataProvider(config)

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建模拟的 HTTP 会话。"""
        session = MagicMock(spec=aiohttp.ClientSession)

        # 创建模拟的响应上下文管理器
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='v_sh600000="1~浦发银行~600000~10.25~10.00~10.10~10000~5000~5000~10.24~100~10.23~200~10.22~300~10.21~400~10.20~500~10.26~150~10.27~250~10.28~350~10.29~450~10.30~550~15:00:00/10.25/100/B~20250208150000~0.15~1.48~10.30~10.05~10.25/10000/102500~10000~102.50~0.10~1.50~-~10.30~10.05~2.50~1025.00~1025.00~1.20~11.00~9.00~0.85~0~0.00~10.15~11.50~9.50~15.00~8.00~1.50~1.50~0.82~6.80~100.00~100.00~银行~上海~19991110";'
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        session.get = MagicMock(return_value=mock_response)
        session.closed = False
        return session

    async def test_get_normal_flow(
        self, provider: TencentStockDataProvider, mock_session: MagicMock
    ) -> None:
        """测试正常数据获取流程。"""
        provider.session = mock_session

        quote = await provider.get("sh600000")

        assert isinstance(quote, StockQuote)
        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.15

    async def test_get_without_session_raises_error(
        self, provider: TencentStockDataProvider
    ) -> None:
        """测试未初始化会话时抛出错误。"""
        with pytest.raises(RuntimeError, match="会话未初始化"):
            await provider.get("sh600000")

    async def test_get_with_network_error(
        self, config: ProviderConfig
    ) -> None:
        """测试网络错误处理。"""
        provider = TencentStockDataProvider(config)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_session.closed = False
        provider.session = mock_session

        with pytest.raises(NetworkError, match="网络请求失败"):
            await provider._get("sh600000")

    async def test_get_with_timeout_error(
        self, config: ProviderConfig
    ) -> None:
        """测试请求超时处理。"""
        provider = TencentStockDataProvider(config)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_session.get = MagicMock(side_effect=TimeoutError())
        mock_session.closed = False
        provider.session = mock_session

        with pytest.raises(NetworkError, match="请求超时"):
            await provider._get("sh600000")
    async def test_get_with_non_200_status(
        self, config: ProviderConfig
    ) -> None:
        """测试非 200 状态码处理。"""
        provider = TencentStockDataProvider(config)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.text = AsyncMock(return_value="Not Found")
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        provider.session = mock_session

        with pytest.raises(ProviderServiceError, match="HTTP 状态码: 404"):
            await provider._get("sh600000")
    async def test_get_with_empty_response(
        self, config: ProviderConfig
    ) -> None:
        """测试空响应处理。"""
        provider = TencentStockDataProvider(config)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.text = AsyncMock(return_value="")
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        provider.session = mock_session

        with pytest.raises(NetworkError, match="返回空响应"):
            await provider._get("sh600000")
    async def test_get_with_whitespace_response(
        self, config: ProviderConfig
    ) -> None:
        """测试空白响应处理。"""
        provider = TencentStockDataProvider(config)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="   ")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.closed = False
        provider.session = mock_session

        with pytest.raises(NetworkError, match="返回空响应"):
            await provider._get("sh600000")

    async def test_api_url_format(self, provider: TencentStockDataProvider, mock_session: MagicMock) -> None:
        """测试 API URL 格式正确。"""
        provider.session = mock_session

        await provider._get("sh600000")

        # 验证调用的 URL
        mock_session.get.assert_called_once_with("https://qt.gtimg.cn/q=sh600000")

    async def test_parser_integration(
        self, provider: TencentStockDataProvider, mock_session: MagicMock
    ) -> None:
        """测试解析器集成。"""
        provider.session = mock_session

        quote = await provider.get("sh600000")

        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.volume == 10000

    async def test_get_invalid_stock_code(self, provider: TencentStockDataProvider) -> None:
        """测试获取无效股票代码。"""
        provider.session = MagicMock(spec=aiohttp.ClientSession)
        provider.session.closed = False

        with pytest.raises(InvalidStockCodeError):
            # 这个测试会在 _validate_stock_code 阶段就失败
            await provider.get("invalid")

    async def test_context_manager_integration(
        self, config: ProviderConfig, mock_session: MagicMock
    ) -> None:
        """测试上下文管理器集成。"""
        provider = TencentStockDataProvider(config, session=mock_session)

        async with provider:
            quote = await provider.get("sh600000")
            assert quote.stock_code == "sh600000"
            assert quote.name == "浦发银行"

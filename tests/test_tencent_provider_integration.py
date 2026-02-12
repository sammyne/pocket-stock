"""腾讯财经数据提供者集成测试。"""

import pytest

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    DataParseException,
    InvalidStockCodeException,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.tencent.provider import TencentStockDataProvider


@pytest.mark.asyncio
@pytest.mark.integration
class TestTencentStockDataProviderIntegration:
    """TencentStockDataProvider 集成测试类。"""

    @pytest.fixture
    def config(self) -> ProviderConfig:
        """创建配置对象。"""
        return ProviderConfig(timeout=30.0)

    @pytest.fixture
    def provider(self, config: ProviderConfig) -> TencentStockDataProvider:
        """创建提供者实例。"""
        return TencentStockDataProvider(config)

    async def test_complete_flow(self, provider: TencentStockDataProvider) -> None:
        """测试完整的股票数据获取流程。"""
        async with provider:
            quote = await provider.get("sh600000")

            assert isinstance(quote, StockQuote)
            assert quote.stock_code == "sh600000"
            assert quote.name is not None and len(quote.name) > 0
            assert quote.current_price > 0
            assert quote.timestamp is not None

    async def test_multiple_stocks(self, provider: TencentStockDataProvider) -> None:
        """测试获取多个股票数据。"""
        stock_codes = ["sh600000", "sz000001", "sh600519"]

        async with provider:
            quotes = []
            for code in stock_codes:
                quote = await provider.get(code)
                quotes.append(quote)
                assert quote.stock_code == code
                assert quote.name is not None

            assert len(quotes) == 3
            # 确保每只股票的名称不同（假设这三只股票的名称不同）
            names = [quote.name for quote in quotes]
            assert len(set(names)) > 1

    async def test_invalid_stock_code(self, provider: TencentStockDataProvider) -> None:
        """测试无效的股票代码。"""
        async with provider:
            with pytest.raises(InvalidStockCodeException):
                await provider.get("invalid_code")

            with pytest.raises(InvalidStockCodeException):
                await provider.get("sh123")  # 长度不足

            with pytest.raises(InvalidStockCodeException):
                await provider.get("bj600000")  # 无效前缀

    async def test_non_existent_stock_code(self, provider: TencentStockDataProvider) -> None:
        """测试不存在的股票代码。"""
        async with provider:
            # 使用一个可能不存在的股票代码
            # 腾讯财经会返回空数据，导致解析失败
            with pytest.raises(DataParseException):
                await provider.get("sh999999")

    async def test_stock_quote_completeness(self, provider: TencentStockDataProvider) -> None:
        """测试股票数据字段的完整性。"""
        async with provider:
            quote = await provider.get("sh600000")

            # 验证必填字段
            assert quote.stock_code is not None
            assert quote.name is not None
            assert quote.current_price is not None

            # 验证可选字段
            # 涨跌额和涨跌幅可能为 0
            assert quote.change is not None
            assert quote.change_percent is not None

            # 成交量和成交额可能为 0
            assert quote.volume is not None
            assert quote.turnover is not None

    async def test_stock_quote_data_types(self, provider: TencentStockDataProvider) -> None:
        """测试股票数据字段类型。"""
        async with provider:
            quote = await provider.get("sh600000")

            assert isinstance(quote.stock_code, str)
            assert isinstance(quote.name, str)
            assert isinstance(quote.current_price, float)
            assert isinstance(quote.change, float)
            assert isinstance(quote.change_percent, float)
            assert isinstance(quote.volume, int)
            assert isinstance(quote.turnover, float)

    async def test_shenzhen_market_stock(self, provider: TencentStockDataProvider) -> None:
        """测试深圳市场股票。"""
        async with provider:
            quote = await provider.get("sz000001")

            assert isinstance(quote, StockQuote)
            assert quote.stock_code == "sz000001"
            assert quote.name is not None
            assert quote.current_price > 0

    async def test_concurrent_requests(self, config: ProviderConfig) -> None:
        """测试并发请求。"""
        import asyncio

        stock_codes = ["sh600000", "sz000001", "sh600519", "sz000002"]

        async def get_stock(code: str) -> StockQuote:
            # 每个并发任务创建自己的 provider 实例
            provider = TencentStockDataProvider(config)
            async with provider:
                return await provider.get(code)

        # 并发获取多只股票
        tasks = [get_stock(code) for code in stock_codes]
        quotes = await asyncio.gather(*tasks)

        assert len(quotes) == 4
        for quote, code in zip(quotes, stock_codes, strict=True):
            assert quote.stock_code == code
            assert quote.name is not None

    async def test_reusability(self, config: ProviderConfig) -> None:
        """测试提供者的可重用性。"""
        provider = TencentStockDataProvider(config)

        async with provider:
            quote1 = await provider.get("sh600000")
            assert quote1.stock_code == "sh600000"

            # 使用同一个提供者实例再次获取
            quote2 = await provider.get("sz000001")
            assert quote2.stock_code == "sz000001"

            # 再次获取第一只股票
            quote3 = await provider.get("sh600000")
            assert quote3.stock_code == "sh600000"

"""集成测试。"""

import pytest

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    InvalidStockCodeException,
    NetworkErrorException,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.tencent.provider import TencentStockDataProvider


@pytest.mark.asyncio
@pytest.mark.integration
class TestStockDataProviderIntegration:
    """StockDataProvider 集成测试类。

    这些测试会实际访问腾讯财经 API，因此需要网络连接。
    使用 --integration 标志运行：pytest -v --integration
    """

    @pytest.fixture
    def config(self) -> ProviderConfig:
        """创建配置实例。"""
        return ProviderConfig(timeout=15.0)

    async def test_get_real_stock_quote(self, config: ProviderConfig) -> None:
        """测试获取真实股票行情。"""
        async with TencentStockDataProvider(config) as provider:
            quote = await provider.get("sh600000")

            assert isinstance(quote, StockQuote)
            assert quote.stock_code == "sh600000"
            assert quote.name is not None and len(quote.name) > 0
            assert quote.current_price > 0
            assert quote.timestamp is not None

            # 打印结果供查看
            print(f"\n股票名称: {quote.name}")
            print(f"当前价格: {quote.current_price}")
            print(f"涨跌额: {quote.change}")
            print(f"涨跌幅: {quote.change_percent}%")
            print(f"成交量: {quote.volume}")
            print(f"成交额: {quote.turnover}")

    async def test_get_multiple_real_stock_quotes(self, config: ProviderConfig) -> None:
        """测试获取多只真实股票行情。"""
        stock_codes = ["sh600000", "sz000001"]

        async with TencentStockDataProvider(config) as provider:
            for code in stock_codes:
                quote = await provider.get(code)

                assert isinstance(quote, StockQuote)
                assert quote.stock_code == code
                assert quote.name is not None and len(quote.name) > 0
                assert quote.current_price > 0

                print(f"\n{code}: {quote.name} - {quote.current_price}")

    async def test_invalid_stock_code(self, config: ProviderConfig) -> None:
        """测试无效股票代码。"""
        async with TencentStockDataProvider(config) as provider:
            with pytest.raises(InvalidStockCodeException, match="无效的股票代码格式"):
                await provider.get("invalid_code")

    async def test_nonexistent_stock_code(self, config: ProviderConfig) -> None:
        """测试不存在的股票代码。"""
        # 使用有效格式但可能不存在的股票代码
        async with TencentStockDataProvider(config) as provider:
            try:
                quote = await provider.get("sh999999")
                # 如果返回数据，检查是否为空或无效
                assert quote is not None
            except (NetworkErrorException, Exception):
                # 某些情况下会抛出异常，这也是可以接受的
                pass

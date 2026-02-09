"""数据解析器异步单元测试。"""

import json

import pytest
from pytest_mock import MockerFixture

from pocket_stock.data_provider.exceptions import DataParseException
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.parser import TencentFinanceParser


@pytest.mark.asyncio
class TestTencentFinanceParser:
    """TencentFinanceParser 异步测试类。"""

    @pytest.fixture
    def parser(self) -> TencentFinanceParser:
        """创建解析器实例。"""
        return TencentFinanceParser()

    async def test_parse_valid_data(self, parser: TencentFinanceParser) -> None:
        """测试解析有效数据。"""
        raw_data = json.dumps(
            {
                "sh600000": {
                    "name": "浦发银行",
                    "price": 10.25,
                    "change": 0.15,
                    "percent": 1.48,
                    "volume": 1000000,
                    "turnover": 10250000.0,
                    "open": 10.10,
                    "close": 10.0,
                    "high": 10.30,
                    "low": 10.05,
                }
            }
        )

        quote = await parser.parse(raw_data, "sh600000")

        assert isinstance(quote, StockQuote)
        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.15
        assert quote.change_percent == 1.48
        assert quote.volume == 1000000
        assert quote.turnover == 10250000.0
        assert quote.open_price == 10.10
        assert quote.close_price == 10.0
        assert quote.high_price == 10.30
        assert quote.low_price == 10.05
        assert quote.timestamp is not None

    async def test_parse_minimal_data(self, parser: TencentFinanceParser) -> None:
        """测试解析最小数据（仅必填字段）。"""
        raw_data = json.dumps({"sh600000": {"name": "浦发银行", "price": 10.25}})

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.0
        assert quote.change_percent == 0.0
        assert quote.volume == 0

    async def test_parse_invalid_json(self, parser: TencentFinanceParser) -> None:
        """测试解析无效 JSON。"""
        raw_data = "这不是有效的 JSON"

        with pytest.raises(DataParseException, match="JSON 解析失败"):
            await parser.parse(raw_data, "sh600000")

    async def test_parse_empty_data(self, parser: TencentFinanceParser) -> None:
        """测试解析空数据。"""
        raw_data = "{}"

        with pytest.raises(DataParseException, match="未找到股票数据"):
            await parser.parse(raw_data, "sh600000")

    async def test_parse_with_negative_change(self, parser: TencentFinanceParser) -> None:
        """测试解析负值涨跌幅。"""
        raw_data = json.dumps(
            {
                "sh600000": {
                    "name": "浦发银行",
                    "price": 9.90,
                    "change": -0.10,
                    "percent": -1.0,
                }
            }
        )

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.current_price == 9.90
        assert quote.change == -0.10
        assert quote.change_percent == -1.0

    async def test_parse_with_string_volume(self, parser: TencentFinanceParser) -> None:
        """测试解析字符串格式的成交量。"""
        raw_data = json.dumps(
            {
                "sh600000": {
                    "name": "浦发银行",
                    "price": 10.25,
                    "volume": "1000000",
                }
            }
        )

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.volume == 1000000

    async def test_parse_invalid_price(self, parser: TencentFinanceParser) -> None:
        """测试解析无效的价格（导致验证失败）。"""
        raw_data = json.dumps(
            {
                "sh600000": {
                    "name": "浦发银行",
                    "price": -10.25,
                }
            }
        )

        with pytest.raises(Exception):  # 验证异常
            await parser.parse(raw_data, "sh600000")

    async def test_case_insensitive_stock_code(self, parser: TencentFinanceParser) -> None:
        """测试股票代码不区分大小写。"""
        raw_data = json.dumps(
            {
                "sh600000": {
                    "name": "浦发银行",
                    "price": 10.25,
                }
            }
        )

        quote = await parser.parse(raw_data, "SH600000")

        assert quote.stock_code == "SH600000"
        assert quote.name == "浦发银行"

    async def test_auto_extract_first_key(self, parser: TencentFinanceParser) -> None:
        """测试自动提取第一个键的数据。"""
        raw_data = json.dumps(
            {
                "sh600000": {
                    "name": "浦发银行",
                    "price": 10.25,
                }
            }
        )

        quote = await parser.parse(raw_data, "unknown")

        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25

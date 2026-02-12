"""数据解析器异步单元测试。"""

import pytest

from pocket_stock.data_provider.exceptions import DataParseException
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.tencent.parser import TencentFinanceParser


@pytest.mark.asyncio
class TestTencentFinanceParser:
    """TencentFinanceParser 异步测试类。"""

    @pytest.fixture
    def parser(self) -> TencentFinanceParser:
        """创建解析器实例。"""
        return TencentFinanceParser()

    async def test_parse_valid_data(self, parser: TencentFinanceParser) -> None:
        """测试解析有效数据。"""
        # 格式：v_sh600000="1~名称~代码~价格~昨收~今开~成交量~..."
        raw_data = 'v_sh600000="1~浦发银行~600000~10.25~10.00~10.10~10000~5000~5000~10.24~100~10.23~200~10.22~300~10.21~400~10.20~500~10.26~150~10.27~250~10.28~350~10.29~450~10.30~550~15:00:00/10.25/100/B~20250208150000~0.15~1.48~10.30~10.05~10.25/10000/102500~10000~102.50~0.10~1.50~-~10.30~10.05~2.50~1025.00~1025.00~1.20~11.00~9.00~0.85~0~0.00~10.15~11.50~9.50~15.00~8.00~1.50~1.50~0.82~6.80~100.00~100.00~银行~上海~19991110"'

        quote = await parser.parse(raw_data, "sh600000")

        assert isinstance(quote, StockQuote)
        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.15
        assert quote.change_percent == 1.48
        assert quote.volume == 10000
        assert quote.turnover == 1025000.0  # 102.50 万元 = 1025000.0 元
        assert quote.open_price == 10.10
        assert quote.close_price == 10.00
        assert quote.high_price == 10.30
        assert quote.low_price == 10.05
        assert quote.timestamp is not None

    async def test_parse_minimal_data(self, parser: TencentFinanceParser) -> None:
        """测试解析最小数据（仅必填字段）。"""
        # 测试缺少某些可选字段的情况
        raw_data = 'v_sh600000="1~浦发银行~600000~10.25~10.00~10.10~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0.00~0.00~0.00~0.00~~0~0~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~0.00~~0.00~0.00~~0.00~0.00~0.00~~0.00~~"'

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.00
        assert quote.change_percent == 0.00
        assert quote.volume == 0

    async def test_parse_invalid_format(self, parser: TencentFinanceParser) -> None:
        """测试解析无效格式。"""
        raw_data = "这不是有效的格式"

        with pytest.raises(DataParseException, match="数据格式错误"):
            await parser.parse(raw_data, "sh600000")

    async def test_parse_empty_data(self, parser: TencentFinanceParser) -> None:
        """测试解析空数据。"""
        raw_data = ""

        with pytest.raises(DataParseException, match="数据格式错误"):
            await parser.parse(raw_data, "sh600000")

    async def test_parse_with_negative_change(self, parser: TencentFinanceParser) -> None:
        """测试解析负值涨跌幅。"""
        raw_data = 'v_sh600000="1~浦发银行~600000~9.90~10.00~9.95~5000~2500~2500~9.89~100~9.88~200~9.87~300~9.86~400~9.85~500~9.91~150~9.92~250~9.93~350~9.94~450~9.95~550~15:00:00/9.90/100/S~20250208150000~-0.10~-1.00~9.95~9.85~9.90/5000/49500~5000~4.95~0.05~1.50~-~9.95~9.85~1.00~512.50~512.50~1.20~11.00~9.00~0.85~0~0.00~9.88~11.00~9.00~12.00~7.00~1.50~1.50~0.80~6.00~50.00~50.00~银行~上海~19991110"'

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.current_price == 9.90
        assert quote.change == -0.10
        assert quote.change_percent == -1.00

    async def test_parse_with_large_volume(self, parser: TencentFinanceParser) -> None:
        """测试解析大成交量。"""
        raw_data = 'v_sh600000="1~浦发银行~600000~10.25~10.00~10.10~1234567~617283~617284~10.24~1000~10.23~2000~10.22~3000~10.21~4000~10.20~5000~10.26~1500~10.27~2500~10.28~3500~10.29~4500~10.30~5500~15:00:00/10.25/1000/B~20250208150000~0.15~1.48~10.30~10.05~10.25/1234567/12654316~1234567~12654.32~0.12~1.50~-~10.30~10.05~2.50~12654.32~12654.32~1.20~11.00~9.00~0.85~0~0.00~10.15~11.50~9.50~15.00~8.00~1.50~1.50~0.82~6.80~100.00~100.00~银行~上海~19991110"'

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.volume == 1234567
        assert quote.turnover == 126543200.0  # 12654.32 万元 = 126543200.0 元

    async def test_parse_invalid_price(self, parser: TencentFinanceParser) -> None:
        """测试解析无效的价格（负值）。"""
        raw_data = 'v_sh600000="1~浦发银行~600000~-10.25~10.00~10.10~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~-20.25~-202.50~0.00~0.00~~0~0~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~~0.00~0.00~0.00~~0.00~0.00~~0.00~0.00~0.00~~0.00~~"'

        with pytest.raises(DataParseException):
            await parser.parse(raw_data, "sh600000")

    async def test_case_insensitive_stock_code(self, parser: TencentFinanceParser) -> None:
        """测试股票代码不区分大小写。"""
        raw_data = 'v_sh600000="1~浦发银行~600000~10.25~10.00~10.10~10000~5000~5000~10.24~100~10.23~200~10.22~300~10.21~400~10.20~500~10.26~150~10.27~250~10.28~350~10.29~450~10.30~550~15:00:00/10.25/100/B~20250208150000~0.15~1.48~10.30~10.05~10.25/10000/102500~10000~102.50~0.10~1.50~-~10.30~10.05~2.50~1025.00~1025.00~1.20~11.00~9.00~0.85~0~0.00~10.15~11.50~9.50~15.00~8.00~1.50~1.50~0.82~6.80~100.00~100.00~银行~上海~19991110"'

        quote = await parser.parse(raw_data, "SH600000")

        assert quote.stock_code == "SH600000"
        assert quote.name == "浦发银行"

    async def test_parse_with_semicolon_ending(self, parser: TencentFinanceParser) -> None:
        """测试解析以分号结尾的数据。"""
        # 腾讯财经实际返回可能包含分号
        raw_data = 'v_sh600000="1~浦发银行~600000~10.25~10.00~10.10~10000~5000~5000~10.24~100~10.23~200~10.22~300~10.21~400~10.20~500~10.26~150~10.27~250~10.28~350~10.29~450~10.30~550~15:00:00/10.25/100/B~20250208150000~0.15~1.48~10.30~10.05~10.25/10000/102500~10000~102.50~0.10~1.50~-~10.30~10.05~2.50~1025.00~1025.00~1.20~11.00~9.00~0.85~0~0.00~10.15~11.50~9.50~15.00~8.00~1.50~1.50~0.82~6.80~100.00~100.00~银行~上海~19991110";'

        quote = await parser.parse(raw_data, "sh600000")

        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.15

"""数据模型单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from pocket_stock.data_provider.exceptions import DataValidationException
from pocket_stock.data_provider.models import StockQuote


class TestStockQuote:
    """StockQuote 测试类。"""

    def test_create_quote(self) -> None:
        """测试创建股票行情对象。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.25,
            change=0.15,
            change_percent=1.48,
            volume=1000000,
            turnover=10250000.0,
        )
        assert quote.stock_code == "sh600000"
        assert quote.name == "浦发银行"
        assert quote.current_price == 10.25
        assert quote.change == 0.15
        assert quote.change_percent == 1.48
        assert quote.volume == 1000000
        assert quote.turnover == 10250000.0

    def test_create_quote_with_defaults(self) -> None:
        """测试使用默认值创建股票行情对象。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.25,
        )
        assert quote.change == 0.0
        assert quote.change_percent == 0.0
        assert quote.volume == 0
        assert quote.turnover == 0.0
        assert quote.open_price is None
        assert quote.close_price is None
        assert quote.high_price is None
        assert quote.low_price is None
        assert quote.timestamp is None

    def test_negative_change(self) -> None:
        """测试负值涨跌幅。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.10,
            change=-0.15,
            change_percent=-1.48,
        )
        assert quote.change == -0.15
        assert quote.change_percent == -1.48

    def test_empty_stock_code_raises_error(self) -> None:
        """测试空股票代码会引发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            StockQuote(
                stock_code="",
                name="浦发银行",
                current_price=10.25,
            )
        assert "stock_code" in str(exc_info.value).lower()

    def test_empty_name_raises_error(self) -> None:
        """测试空股票名称会引发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            StockQuote(
                stock_code="sh600000",
                name="",
                current_price=10.25,
            )
        assert "name" in str(exc_info.value).lower()

    def test_negative_price_raises_error(self) -> None:
        """测试负价格会引发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            StockQuote(
                stock_code="sh600000",
                name="浦发银行",
                current_price=-10.25,
            )
        assert "current_price" in str(exc_info.value).lower()

    def test_negative_volume_raises_error(self) -> None:
        """测试负成交量会引发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            StockQuote(
                stock_code="sh600000",
                name="浦发银行",
                current_price=10.25,
                volume=-1000,
            )
        assert "volume" in str(exc_info.value).lower()

    def test_negative_open_price_raises_error(self) -> None:
        """测试负开盘价会引发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            StockQuote(
                stock_code="sh600000",
                name="浦发银行",
                current_price=10.25,
                open_price=-10.0,
            )
        assert "open_price" in str(exc_info.value).lower()

    def test_model_serialization(self) -> None:
        """测试模型序列化。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.25,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 测试 model_dump
        data_dict = quote.model_dump()
        assert data_dict["stock_code"] == "sh600000"
        assert data_dict["name"] == "浦发银行"
        assert data_dict["current_price"] == 10.25

        # 测试 model_dump_json
        json_str = quote.model_dump_json()
        assert "sh600000" in json_str
        assert "浦发银行" in json_str

"""analyse_stock 主函数单元测试。"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pocket_stock.data_provider.models import StockQuote
from pocket_stock.llm import analyse_stock
from pocket_stock.llm.exceptions import (
    ConfigurationError,
    LLMAnalysisError,
    LLMApiTimeoutError,
    LLMAuthenticationError,
)
from pocket_stock.llm.models import StockAnalysisResult
from pocket_stock.search.models import (
    SearchResponse,
    SearchResult,
    StockSearchDimension,
    StockSearchResponse,
)


class TestAnalyseStock:
    """analyse_stock 主函数测试类。"""

    @pytest.fixture
    def sample_stock_quote(self) -> StockQuote:
        """创建测试用的股票行情数据。"""
        return StockQuote(
            stock_code="sh600519",
            name="贵州茅台",
            current_price=1800.00,
            change=10.00,
            change_percent=0.56,
            volume=10000,
            turnover=18000000.00,
            open_price=1790.00,
            close_price=1795.00,
            high_price=1805.00,
            low_price=1788.00,
        )

    @pytest.fixture
    def sample_stock_news(self) -> StockSearchResponse:
        """创建测试用的股票新闻数据。"""
        search_response = SearchResponse(
            query="贵州茅台",
            results=[
                SearchResult(
                    title="贵州茅台发布2024年业绩报告",
                    content="贵州茅台2024年业绩超预期...",
                    url="https://example.com/news1",
                    source="证券时报",
                    published_date=datetime.now(),
                    score=0.9,
                )
            ],
            response_time=0.5,
        )

        return StockSearchResponse(
            stock_name="贵州茅台",
            dimensions={StockSearchDimension.LATEST_NEWS: search_response},
            total_time=0.5,
        )

    @pytest.fixture
    def sample_analysis_result(self) -> StockAnalysisResult:
        """创建测试用的分析结果。"""
        from pocket_stock.llm.models import ChecklistItem, PositionSuggestion, TargetPrices

        return StockAnalysisResult(
            stock_name="贵州茅台",
            conclusion="该买",
            position_suggestion=PositionSuggestion(
                no_position="建议在1780元附近分批建仓",
                has_position="建议继续持有，目标价2000元",
            ),
            target_prices=TargetPrices(
                buy_price=1780.00,
                stop_loss_price=1750.00,
                target_price=2000.00,
            ),
            checklist=[
                ChecklistItem(content="基本面稳健", status="✅"),
                ChecklistItem(content="技术面良好", status="✅"),
                ChecklistItem(content="资金面充裕", status="✅"),
                ChecklistItem(content="政策面支持", status="⚠️"),
                ChecklistItem(content="风险可控", status="✅"),
            ],
        )

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_success(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
        sample_analysis_result: StockAnalysisResult,
    ) -> None:
        """测试成功的股票分析。"""
        # 设置 mock
        mock_analyser_instance = Mock()
        mock_analyser_instance.analyse.return_value = sample_analysis_result
        mock_analyser_class.from_env.return_value = mock_analyser_instance

        # 执行分析
        result = analyse_stock(sample_stock_quote, sample_stock_news)

        # 验证结果
        assert result == sample_analysis_result
        mock_analyser_class.from_env.assert_called_once()
        mock_analyser_instance.analyse.assert_called_once_with(sample_stock_quote, sample_stock_news)

    def test_analyse_stock_none_quote(self, sample_stock_news: StockSearchResponse) -> None:
        """测试 stock_quote 为 None 的情况。"""
        with pytest.raises(ValueError) as exc_info:
            analyse_stock(None, sample_stock_news)  # type: ignore[arg-type]

        assert "stock_quote 不能为 None" in str(exc_info.value)

    def test_analyse_stock_none_news(self, sample_stock_quote: StockQuote) -> None:
        """测试 stock_news 为 None 的情况。"""
        with pytest.raises(ValueError) as exc_info:
            analyse_stock(sample_stock_quote, None)  # type: ignore[arg-type]

        assert "stock_news 不能为 None" in str(exc_info.value)

    def test_analyse_stock_empty_stock_code(self, sample_stock_news: StockSearchResponse) -> None:
        """测试股票代码为空的情况。"""
        # 由于 StockQuote 使用 Pydantic 验证，无法直接创建空字符串的实例
        # 我们测试在创建对象时应该会失败
        with pytest.raises(ValueError) as exc_info:
            StockQuote(
                stock_code="",  # 空的股票代码 - Pydantic 会验证
                name="贵州茅台",
                current_price=1800.00,
            )

        # 验证 Pydantic 抛出了验证错误
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_analyse_stock_empty_stock_name(self, sample_stock_news: StockSearchResponse) -> None:
        """测试股票名称为空的情况。"""
        # 由于 StockQuote 使用 Pydantic 验证，无法直接创建空字符串的实例
        with pytest.raises(ValueError) as exc_info:
            StockQuote(
                stock_code="sh600519",
                name="",  # 空的股票名称 - Pydantic 会验证
                current_price=1800.00,
            )

        assert "String should have at least 1 character" in str(exc_info.value)

    def test_analyse_stock_negative_price(self, sample_stock_news: StockSearchResponse) -> None:
        """测试价格为负数的情况。"""
        # 由于 StockQuote 使用 Pydantic 验证，无法直接创建负价格的实例
        with pytest.raises(ValueError) as exc_info:
            StockQuote(
                stock_code="sh600519",
                name="贵州茅台",
                current_price=-100.00,  # 负数价格 - Pydantic 会验证
            )

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_analyse_stock_none_price(self, sample_stock_news: StockSearchResponse) -> None:
        """测试价格为 None 的情况。"""
        # 由于 StockQuote 使用 Pydantic 验证，无法直接创建 None 价格的实例
        with pytest.raises(ValueError) as exc_info:
            StockQuote(
                stock_code="sh600519",
                name="贵州茅台",
                current_price=None,  # type: ignore[arg-type]
            )

        assert "Input should be a valid number" in str(exc_info.value)

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_timeout_error(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试超时错误。"""
        mock_analyser_instance = Mock()
        mock_analyser_instance.analyse.side_effect = LLMApiTimeoutError("API timeout")
        mock_analyser_class.from_env.return_value = mock_analyser_instance

        with pytest.raises(LLMApiTimeoutError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_auth_error(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试认证错误。"""
        mock_analyser_instance = Mock()
        mock_analyser_instance.analyse.side_effect = LLMAuthenticationError("Invalid API key")
        mock_analyser_class.from_env.return_value = mock_analyser_instance

        with pytest.raises(LLMAuthenticationError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_configuration_error(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试配置错误。"""
        mock_analyser_class.from_env.side_effect = ConfigurationError("Missing API key")

        with pytest.raises(ConfigurationError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_unknown_error(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试未知错误。"""
        mock_analyser_instance = Mock()
        mock_analyser_instance.analyse.side_effect = ValueError("Unknown error")
        mock_analyser_class.from_env.return_value = mock_analyser_instance

        with pytest.raises(LLMAnalysisError) as exc_info:
            analyse_stock(sample_stock_quote, sample_stock_news)

        assert "股票分析失败" in str(exc_info.value)

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_with_empty_news(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_analysis_result: StockAnalysisResult,
    ) -> None:
        """测试空新闻数据的情况。"""
        empty_news = StockSearchResponse(
            stock_name="贵州茅台",
            dimensions={},
            total_time=0.0,
        )

        mock_analyser_instance = Mock()
        mock_analyser_instance.analyse.return_value = sample_analysis_result
        mock_analyser_class.from_env.return_value = mock_analyser_instance

        result = analyse_stock(sample_stock_quote, empty_news)

        assert result == sample_analysis_result
        mock_analyser_instance.analyse.assert_called_once_with(sample_stock_quote, empty_news)

    @patch("pocket_stock.llm.main.LLMStockAnalyser")
    def test_analyse_stock_with_multiple_news_dimensions(
        self,
        mock_analyser_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
        sample_analysis_result: StockAnalysisResult,
    ) -> None:
        """测试多个新闻维度的情况。"""
        # 添加更多维度
        risk_response = SearchResponse(
            query="贵州茅台风险",
            results=[
                SearchResult(
                    title="贵州茅台面临监管风险",
                    content="监管部门对白酒行业...",
                    url="https://example.com/news2",
                    source="财联社",
                    published_date=datetime.now(),
                    score=0.8,
                )
            ],
            response_time=0.3,
        )

        sample_stock_news.dimensions[StockSearchDimension.RISK_ANALYSIS] = risk_response

        mock_analyser_instance = Mock()
        mock_analyser_instance.analyse.return_value = sample_analysis_result
        mock_analyser_class.from_env.return_value = mock_analyser_instance

        result = analyse_stock(sample_stock_quote, sample_stock_news)

        assert result == sample_analysis_result
        assert len(sample_stock_news.dimensions) == 2

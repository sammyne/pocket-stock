"""LLM 模块集成测试。"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from pocket_stock.data_provider.models import StockQuote
from pocket_stock.llm import analyse_stock
from pocket_stock.llm.exceptions import (
    LLMAnalysisError,
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMServiceError,
)
from pocket_stock.llm.models import (
    ChecklistItem,
    PositionSuggestion,
    StockAnalysisResult,
    TargetPrices,
)
from pocket_stock.search.models import (
    SearchResponse,
    SearchResult,
    StockSearchDimension,
    StockSearchResponse,
)


@pytest.mark.integration
class TestLLMIntegration:
    """LLM 模块集成测试类。

    这些测试使用 mock 的 LLM 服务模拟各种场景，
    测试 analyse_stock 函数的端到端流程。
    """

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """设置测试环境变量。"""
        monkeypatch.setenv("OPENAI_MODEL", "test-model")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://test.api/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

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
        news_response = SearchResponse(
            query="贵州茅台",
            results=[
                SearchResult(
                    title="贵州茅台发布2024年业绩报告",
                    content="贵州茅台2024年业绩超预期，净利润同比增长15%...",
                    url="https://example.com/news1",
                    source="证券时报",
                    published_date=datetime.now(),
                    score=0.9,
                )
            ],
            response_time=0.5,
        )

        risk_response = SearchResponse(
            query="贵州茅台风险",
            results=[
                SearchResult(
                    title="贵州茅台面临监管风险",
                    content="监管部门对白酒行业出台新政策...",
                    url="https://example.com/news2",
                    source="财联社",
                    published_date=datetime.now(),
                    score=0.8,
                )
            ],
            response_time=0.3,
        )

        return StockSearchResponse(
            stock_name="贵州茅台",
            dimensions={
                StockSearchDimension.LATEST_NEWS: news_response,
                StockSearchDimension.RISK_ANALYSIS: risk_response,
            },
            total_time=0.8,
        )

    @pytest.fixture
    def mock_buy_result(self) -> StockAnalysisResult:
        """模拟买入建议的 LLM 结果。"""
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

    @pytest.fixture
    def mock_sell_result(self) -> StockAnalysisResult:
        """模拟卖出建议的 LLM 结果。"""
        return StockAnalysisResult(
            stock_name="贵州茅台",
            conclusion="该卖",
            position_suggestion=PositionSuggestion(
                no_position="观望等待",
                has_position="建议减仓或清仓",
            ),
            target_prices=TargetPrices(
                buy_price=None,
                stop_loss_price=None,
                target_price=None,
            ),
            checklist=[
                ChecklistItem(content="基本面恶化", status="❌"),
                ChecklistItem(content="技术面转弱", status="❌"),
                ChecklistItem(content="资金面紧张", status="❌"),
                ChecklistItem(content="政策面不利", status="⚠️"),
                ChecklistItem(content="风险较高", status="❌"),
            ],
        )

    @pytest.fixture
    def mock_wait_result(self) -> StockAnalysisResult:
        """模拟观望建议的 LLM 结果。"""
        return StockAnalysisResult(
            stock_name="贵州茅台",
            conclusion="该等",
            position_suggestion=PositionSuggestion(
                no_position="保持观望，等待更好的入场时机",
                has_position="继续持有，密切关注",
            ),
            target_prices=TargetPrices(
                buy_price=1750.00,
                stop_loss_price=1730.00,
                target_price=1950.00,
            ),
            checklist=[
                ChecklistItem(content="基本面平稳", status="✅"),
                ChecklistItem(content="技术面震荡", status="⚠️"),
                ChecklistItem(content="资金面中性", status="⚠️"),
                ChecklistItem(content="政策面不明", status="⚠️"),
                ChecklistItem(content="风险中等", status="⚠️"),
            ],
        )

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_end_to_end_buy_recommendation(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
        mock_buy_result: StockAnalysisResult,
    ) -> None:
        """测试端到端的买入建议流程。"""
        # 设置 mock LLM 响应
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_buy_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        # 执行分析
        result = analyse_stock(sample_stock_quote, sample_stock_news)

        # 验证结果
        assert isinstance(result, StockAnalysisResult)
        assert result.stock_name == "贵州茅台"
        assert result.conclusion == "该买"
        assert "分批建仓" in result.position_suggestion.no_position
        assert "继续持有" in result.position_suggestion.has_position
        assert result.target_prices.buy_price == 1780.00
        assert result.target_prices.stop_loss_price == 1750.00
        assert result.target_prices.target_price == 2000.00
        assert len(result.checklist) == 5

        # 验证 LLM 被正确调用
        mock_structured_llm.invoke.assert_called_once()

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_end_to_end_sell_recommendation(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
        mock_sell_result: StockAnalysisResult,
    ) -> None:
        """测试端到端的卖出建议流程。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_sell_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        result = analyse_stock(sample_stock_quote, sample_stock_news)

        assert result.conclusion == "该卖"
        assert "观望" in result.position_suggestion.no_position
        assert "减仓" in result.position_suggestion.has_position
        assert result.target_prices.buy_price is None
        assert result.target_prices.stop_loss_price is None
        assert result.target_prices.target_price is None

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_end_to_end_wait_recommendation(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
        mock_wait_result: StockAnalysisResult,
    ) -> None:
        """测试端到端的观望建议流程。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_wait_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        result = analyse_stock(sample_stock_quote, sample_stock_news)

        assert result.conclusion == "该等"
        assert "观望" in result.position_suggestion.no_position
        assert "密切关注" in result.position_suggestion.has_position
        assert result.target_prices.buy_price == 1750.00
        assert result.target_prices.stop_loss_price == 1730.00
        assert result.target_prices.target_price == 1950.00

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_timeout_scenario(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试超时场景。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = TimeoutError("Request timeout")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        with pytest.raises(LLMApiTimeoutError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_authentication_error_scenario(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试认证错误场景。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = PermissionError("Invalid API key")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        with pytest.raises(LLMAuthenticationError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_invalid_json_response(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试无效 JSON 响应场景。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = Exception("Invalid response")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        with pytest.raises(LLMServiceError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.config.LLMConfig")
    def test_missing_configuration(
        self,
        mock_llm_config_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试缺少配置的场景。"""
        # 配置 LLMConfig 在初始化时抛出 ValidationError（模拟缺少环境变量）
        mock_llm_config_class.side_effect = ValidationError.from_exception_data(
            title="LLMConfig",
            line_errors=[
                {
                    "type": "missing",
                    "loc": ("OPENAI_MODEL",),
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ("OPENAI_API_BASE_URL",),
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ("OPENAI_API_KEY",),
                    "msg": "Field required",
                    "input": {},
                },
            ],
        )

        # 配置加载应该失败
        with pytest.raises(LLMAnalysisError):
            analyse_stock(sample_stock_quote, sample_stock_news)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_empty_news_dimensions(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        mock_buy_result: StockAnalysisResult,
    ) -> None:
        """测试空新闻维度的场景。"""
        empty_news = StockSearchResponse(
            stock_name="贵州茅台",
            dimensions={},
            total_time=0.0,
        )

        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_buy_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        result = analyse_stock(sample_stock_quote, empty_news)

        assert isinstance(result, StockAnalysisResult)
        # 应该仍然能够进行分析，只是没有新闻数据

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_multiple_news_dimensions(
        self,
        mock_chat_openai_class: Mock,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
        mock_buy_result: StockAnalysisResult,
    ) -> None:
        """测试多个新闻维度的场景。"""
        # 添加更多维度
        analysis_response = SearchResponse(
            query="贵州茅台分析",
            results=[
                SearchResult(
                    title="机构看好贵州茅台",
                    content="多家券商维持买入评级...",
                    url="https://example.com/news3",
                    source="券商研报",
                    published_date=datetime.now(),
                    score=0.85,
                )
            ],
            response_time=0.4,
        )

        sample_stock_news.dimensions[StockSearchDimension.INSTITUTION_ANALYSIS] = analysis_response

        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_buy_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        result = analyse_stock(sample_stock_quote, sample_stock_news)

        assert isinstance(result, StockAnalysisResult)
        assert len(sample_stock_news.dimensions) == 3

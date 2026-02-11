"""LLM 股票分析器单元测试。"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pocket_stock.data_provider.models import StockQuote
from pocket_stock.llm.analyser import LLMStockAnalyser
from pocket_stock.llm.config import LLMConfig
from pocket_stock.llm.exceptions import (
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMServiceError,
    NetworkConnectionError,
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


class TestLLMStockAnalyser:
    """LLMStockAnalyser 测试类。"""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """设置测试环境变量。"""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    @pytest.fixture
    def mock_config(self) -> LLMConfig:
        """创建测试用的 LLM 配置。"""
        return LLMConfig(
            openai_model="gpt-4",
            openai_api_base_url="https://api.openai.com/v1",
            openai_api_key="sk-test-key",
        )

    @pytest.fixture
    def analyser(self, mock_config: LLMConfig) -> LLMStockAnalyser:
        """创建测试用的分析器实例。"""
        return LLMStockAnalyser(mock_config)

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

    def test_init_with_config(self, mock_config: LLMConfig) -> None:
        """测试使用配置对象初始化分析器。"""
        analyser = LLMStockAnalyser(mock_config)

        assert analyser._config == mock_config
        assert analyser._llm is not None

    @patch("pocket_stock.llm.analyser.LLMConfig")
    def test_init_without_config(self, mock_llm_config_class: Mock) -> None:
        """测试不使用配置对象初始化分析器。"""
        mock_config = Mock(
            openai_model="gpt-4",
            openai_api_base_url="https://api.openai.com/v1",
            openai_api_key="sk-test-key",
        )
        mock_llm_config_class.return_value = mock_config

        analyser = LLMStockAnalyser()

        mock_llm_config_class.assert_called_once()
        assert analyser._config == mock_config

    def test_build_prompt(
        self, analyser: LLMStockAnalyser, sample_stock_quote: StockQuote, sample_stock_news: StockSearchResponse
    ) -> None:
        """测试提示词构建。"""
        prompt = analyser._build_prompt(sample_stock_quote, sample_stock_news)

        assert "贵州茅台" in prompt
        assert "sh600519" in prompt
        assert "1800.00" in prompt
        assert "业绩超预期" in prompt

    def test_format_news_with_dimensions(
        self, analyser: LLMStockAnalyser, sample_stock_news: StockSearchResponse
    ) -> None:
        """测试有维度的新闻格式化。"""
        news_text = analyser._format_news(sample_stock_news)

        assert "最新资讯" in news_text
        assert "贵州茅台发布2024年业绩报告" in news_text
        assert "证券时报" in news_text

    def test_format_news_without_dimensions(self, analyser: LLMStockAnalyser) -> None:
        """测试没有维度的新闻格式化。"""
        news = StockSearchResponse(stock_name="测试股票", dimensions={}, total_time=0.0)
        news_text = analyser._format_news(news)

        assert "暂无相关新闻资讯" in news_text

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_analyse_success(
        self,
        mock_chat_openai_class: Mock,
        analyser: LLMStockAnalyser,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试成功的股票分析。"""
        # 创建预期的结构化输出
        expected_result = StockAnalysisResult(
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

        # 设置 mock 响应：with_structured_output 返回一个新的 mock，其 invoke 返回结构化结果
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        # 重新创建分析器以使用 mock 的 ChatOpenAI
        analyser = LLMStockAnalyser(analyser._config)

        # 执行分析
        result = analyser.analyse(sample_stock_quote, sample_stock_news)

        # 验证结果
        assert isinstance(result, StockAnalysisResult)
        assert result.stock_name == "贵州茅台"
        assert result.conclusion == "该买"
        assert result.position_suggestion.no_position == "建议在1780元附近分批建仓"
        assert result.position_suggestion.has_position == "建议继续持有，目标价2000元"
        assert result.target_prices.buy_price == 1780.00
        assert result.target_prices.stop_loss_price == 1750.00
        assert result.target_prices.target_price == 2000.00
        assert len(result.checklist) == 5

        # 验证 LLM 被正确调用
        mock_structured_llm.invoke.assert_called_once()

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_analyse_timeout_error(
        self,
        mock_chat_openai_class: Mock,
        analyser: LLMStockAnalyser,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试超时错误处理。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = TimeoutError("Request timeout")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        analyser = LLMStockAnalyser(analyser._config)

        with pytest.raises(LLMApiTimeoutError) as exc_info:
            analyser.analyse(sample_stock_quote, sample_stock_news)

        assert "超时" in str(exc_info.value)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_analyse_auth_error(
        self,
        mock_chat_openai_class: Mock,
        analyser: LLMStockAnalyser,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试认证错误处理。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = PermissionError("Invalid API key")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        analyser = LLMStockAnalyser(analyser._config)

        with pytest.raises(LLMAuthenticationError) as exc_info:
            analyser.analyse(sample_stock_quote, sample_stock_news)

        assert "认证" in str(exc_info.value)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_analyse_connection_error(
        self,
        mock_chat_openai_class: Mock,
        analyser: LLMStockAnalyser,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试连接错误处理。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = ConnectionError("Connection failed")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        analyser = LLMStockAnalyser(analyser._config)

        with pytest.raises(NetworkConnectionError) as exc_info:
            analyser.analyse(sample_stock_quote, sample_stock_news)

        assert "无法连接" in str(exc_info.value)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_analyse_service_error(
        self,
        mock_chat_openai_class: Mock,
        analyser: LLMStockAnalyser,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试服务错误处理。"""
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = Exception("Internal server error")
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        analyser = LLMStockAnalyser(analyser._config)

        with pytest.raises(LLMServiceError) as exc_info:
            analyser.analyse(sample_stock_quote, sample_stock_news)

        assert "服务返回错误" in str(exc_info.value)

    @patch("pocket_stock.llm.analyser.ChatOpenAI")
    def test_sell_recommendation(
        self,
        mock_chat_openai_class: Mock,
        analyser: LLMStockAnalyser,
        sample_stock_quote: StockQuote,
        sample_stock_news: StockSearchResponse,
    ) -> None:
        """测试卖出建议（买入价为 null）。"""
        expected_result = StockAnalysisResult(
            stock_name="贵州茅台",
            conclusion="该卖",
            position_suggestion=PositionSuggestion(
                no_position="观望",
                has_position="建议减仓",
            ),
            target_prices=TargetPrices(
                buy_price=None,
                stop_loss_price=None,
                target_price=None,
            ),
            checklist=[
                ChecklistItem(content="技术面转弱", status="❌"),
                ChecklistItem(content="成交量萎缩", status="⚠️"),
                ChecklistItem(content="负面新闻增多", status="❌"),
                ChecklistItem(content="支撑位破位", status="❌"),
                ChecklistItem(content="资金流出", status="⚠️"),
            ],
        )

        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_chat_openai_class.return_value.with_structured_output.return_value = mock_structured_llm

        analyser = LLMStockAnalyser(analyser._config)

        result = analyser.analyse(sample_stock_quote, sample_stock_news)

        assert result.conclusion == "该卖"
        assert result.target_prices.buy_price is None
        assert result.target_prices.stop_loss_price is None
        assert result.target_prices.target_price is None

"""Web 模块单元测试。"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pocket_stock.cli.web import (
    _format_turnover,
    _format_volume,
    analyse_stock_with_llm,
    fetch_stock_quote,
    format_error_message,
    render_analysis_result,
    render_search_results,
    render_stock_quote,
    search_stock_news,
    validate_stock_code,
)
from pocket_stock.data_provider.exceptions import (
    DataParseError,
    DataValidationError,
    InvalidStockCodeError,
    NetworkError,
    ProviderServiceError,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.llm import (
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMServiceError,
    NetworkConnectionError,
    StockAnalysisResult,
    TargetPrices,
)
from pocket_stock.llm.models import ChecklistItem, PositionSuggestion
from pocket_stock.search.exceptions import (
    AuthenticationError as SearchAuthenticationError,
)
from pocket_stock.search.exceptions import (
    ConfigurationError as SearchConfigurationError,
)
from pocket_stock.search.exceptions import (
    MissingAPIKeyError as SearchMissingAPIKeyError,
)
from pocket_stock.search.exceptions import (
    NetworkError as SearchNetworkError,
)
from pocket_stock.search.exceptions import (
    RateLimitError,
    SearchError,
)
from pocket_stock.search.exceptions import (
    ServiceError as SearchServiceError,
)
from pocket_stock.search.exceptions import (
    ValidationError as SearchValidationError,
)


class TestValidateStockCode:
    """股票代码验证测试类。"""

    def test_valid_sh_code(self) -> None:
        """测试有效的上海股票代码。"""
        is_valid, error = validate_stock_code("sh600000")
        assert is_valid is True
        assert error is None

    def test_valid_sz_code(self) -> None:
        """测试有效的深圳股票代码。"""
        is_valid, error = validate_stock_code("sz000001")
        assert is_valid is True
        assert error is None

    def test_uppercase_code(self) -> None:
        """测试大写股票代码。"""
        is_valid, error = validate_stock_code("SH600000")
        assert is_valid is True
        assert error is None

    def test_code_with_spaces(self) -> None:
        """测试带空格的股票代码。"""
        is_valid, error = validate_stock_code("  sh600000  ")
        assert is_valid is True
        assert error is None

    def test_empty_code(self) -> None:
        """测试空股票代码。"""
        is_valid, error = validate_stock_code("")
        assert is_valid is False
        assert error == "股票代码不能为空"

    def test_whitespace_only_code(self) -> None:
        """测试只有空白的股票代码。"""
        is_valid, error = validate_stock_code("   ")
        # 空白会被 strip 掉，然后格式验证会失败
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    def test_invalid_prefix(self) -> None:
        """测试无效前缀。"""
        is_valid, error = validate_stock_code("bj600000")
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    def test_missing_prefix(self) -> None:
        """测试缺少前缀。"""
        is_valid, error = validate_stock_code("600000")
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    def test_short_code(self) -> None:
        """测试过短的代码。"""
        is_valid, error = validate_stock_code("sh12345")
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    def test_long_code(self) -> None:
        """测试过长的代码。"""
        is_valid, error = validate_stock_code("sh1234567")
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    def test_code_with_letters(self) -> None:
        """测试包含字母的代码。"""
        is_valid, error = validate_stock_code("sh60000a")
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    def test_code_with_special_chars(self) -> None:
        """测试包含特殊字符的代码。"""
        is_valid, error = validate_stock_code("sh60000-")
        assert is_valid is False
        assert error == "股票代码格式无效，请使用 sh600000 或 sz000001 格式"


class TestFormatErrorMessage:
    """错误消息格式化测试类。"""

    def test_invalid_stock_code_exception(self) -> None:
        """测试股票代码无效异常。"""
        e = InvalidStockCodeError("股票代码格式无效")
        msg = format_error_message(e, "sh123")
        assert "股票代码格式无效" in msg
        assert "sh123" in msg
        assert "sh 或 sz 开头" in msg

    def test_network_error_exception(self) -> None:
        """测试网络错误异常。"""
        e = NetworkError("sh600000", "Connection timeout")
        msg = format_error_message(e, "sh600000")
        assert "网络连接失败" in msg
        assert "sh600000" in msg
        assert "Connection timeout" in msg

    def test_provider_service_error_exception(self) -> None:
        """测试数据服务异常。"""
        e = ProviderServiceError("sh600000", 500, "Internal Server Error")
        msg = format_error_message(e, "sh600000")
        assert "数据服务异常" in msg
        assert "500" in msg
        assert "Internal Server Error" in msg

    def test_data_parse_exception(self) -> None:
        """测试数据解析异常。"""
        e = DataParseError("sh600000", "Invalid JSON format")
        msg = format_error_message(e, "sh600000")
        assert "数据解析失败" in msg
        assert "Invalid JSON format" in msg

    def test_data_validation_exception(self) -> None:
        """测试数据验证异常。"""
        e = DataValidationError("Price cannot be negative")
        msg = format_error_message(e, "sh600000")
        assert "数据解析失败" in msg
        assert "Price cannot be negative" in msg

    def test_missing_api_key_error(self) -> None:
        """测试缺少 API Key 异常。"""
        e = SearchMissingAPIKeyError("TAVILY_API_KEY 环境变量未设置")
        msg = format_error_message(e)
        assert "未配置 API Key" in msg
        assert "TAVILY_API_KEY" in msg

    def test_authentication_error(self) -> None:
        """测试认证失败异常。"""
        e = SearchAuthenticationError(message="Invalid API Key")
        msg = format_error_message(e)
        assert "API 认证失败" in msg
        assert "TAVILY_API_KEY" in msg

    def test_rate_limit_error(self) -> None:
        """测试速率限制异常。"""
        e = RateLimitError(limit="100 requests per minute")
        msg = format_error_message(e)
        assert "达到速率限制" in msg
        assert "100 requests per minute" in msg

    def test_validation_error_exception(self) -> None:
        """测试搜索服务验证错误。"""
        e = SearchValidationError(message="Invalid parameter")
        msg = format_error_message(e)
        assert "配置或参数错误" in msg
        assert "Invalid parameter" in msg

    def test_configuration_error_exception(self) -> None:
        """测试搜索服务配置错误。"""
        e = SearchConfigurationError(message="Missing configuration")
        msg = format_error_message(e)
        assert "配置或参数错误" in msg
        assert "Missing configuration" in msg

    def test_network_error_search_exception(self) -> None:
        """测试搜索服务网络错误。"""
        e = SearchNetworkError(message="Network timeout")
        msg = format_error_message(e)
        assert "请求失败" in msg
        assert "Network timeout" in msg

    def test_service_error_exception(self) -> None:
        """测试搜索服务错误。"""
        e = SearchServiceError(message="Service unavailable")
        msg = format_error_message(e)
        assert "请求失败" in msg
        assert "Service unavailable" in msg

    def test_search_error_exception(self) -> None:
        """测试搜索服务通用异常。"""
        e = SearchError(message="Search failed")
        msg = format_error_message(e)
        assert "搜索服务异常" in msg
        assert "Search failed" in msg

    def test_llm_api_timeout_error(self) -> None:
        """测试 LLM API 超时异常。"""
        e = LLMApiTimeoutError()
        msg = format_error_message(e)
        assert "API 调用超时" in msg

    def test_llm_authentication_error(self) -> None:
        """测试 LLM 认证失败异常。"""
        e = LLMAuthenticationError()
        msg = format_error_message(e)
        assert "API 认证失败" in msg
        assert "OPENAI_API_KEY" in msg

    def test_network_connection_error(self) -> None:
        """测试 LLM 网络连接错误。"""
        e = NetworkConnectionError()
        msg = format_error_message(e)
        assert "无法连接到 LLM 服务" in msg

    def test_llm_service_error(self) -> None:
        """测试 LLM 服务错误。"""
        e = LLMServiceError()
        msg = format_error_message(e)
        assert "服务返回错误" in msg

    def test_generic_exception(self) -> None:
        """测试通用异常。"""
        e = ValueError("Some unexpected error")
        msg = format_error_message(e, "sh600000")
        assert "发生未知错误" in msg
        assert "sh600000" in msg
        assert "ValueError" in msg
        assert "Some unexpected error" in msg

    def test_error_without_stock_code(self) -> None:
        """测试没有股票代码的错误。"""
        e = ValueError("Some error")
        msg = format_error_message(e)
        assert "未知" in msg


class TestFormatVolume:
    """成交量格式化测试类。"""

    def test_none_volume(self) -> None:
        """测试 None 成交量。"""
        result = _format_volume(None)
        assert result == "0"

    def test_zero_volume(self) -> None:
        """测试零成交量。"""
        result = _format_volume(0)
        assert result == "0"

    def test_small_volume(self) -> None:
        """测试小成交量。"""
        result = _format_volume(5000)
        assert result == "5000 股"

    def test_wan_volume(self) -> None:
        """测试万级成交量。"""
        result = _format_volume(150000)
        assert result == "15.00 万股"

    def test_yi_volume(self) -> None:
        """测试亿级成交量。"""
        result = _format_volume(350000000)
        assert result == "3.50 亿股"

    def test_exact_wan_volume(self) -> None:
        """测试准确的万级成交量。"""
        result = _format_volume(100000)
        assert result == "10.00 万股"

    def test_exact_yi_volume(self) -> None:
        """测试准确的亿级成交量。"""
        result = _format_volume(100000000)
        assert result == "1.00 亿股"


class TestFormatTurnover:
    """成交额格式化测试类。"""

    def test_none_turnover(self) -> None:
        """测试 None 成交额。"""
        result = _format_turnover(None)
        assert result == "0 元"

    def test_zero_turnover(self) -> None:
        """测试零成交额。"""
        result = _format_turnover(0.0)
        assert result == "0 元"

    def test_small_turnover(self) -> None:
        """测试小成交额。"""
        result = _format_turnover(5000.0)
        assert result == "5000.00 元"

    def test_wan_turnover(self) -> None:
        """测试万级成交额。"""
        result = _format_turnover(150000.0)
        assert result == "15.00 万元"

    def test_yi_turnover(self) -> None:
        """测试亿级成交额。"""
        result = _format_turnover(350000000.0)
        assert result == "3.50 亿元"

    def test_exact_wan_turnover(self) -> None:
        """测试准确的万级成交额。"""
        result = _format_turnover(100000.0)
        assert result == "10.00 万元"

    def test_exact_yi_turnover(self) -> None:
        """测试准确的亿级成交额。"""
        result = _format_turnover(100000000.0)
        assert result == "1.00 亿元"


class TestFetchStockQuote:
    """股票行情获取测试类。"""

    @pytest.mark.asyncio
    async def test_fetch_quote_success(self) -> None:
        """测试成功获取股票行情。"""
        mock_quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.5,
            change=0.5,
            change_percent=5.0,
        )

        with patch("pocket_stock.cli.web.TencentStockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            # 正确设置 async context manager
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get = AsyncMock(return_value=mock_quote)

            result = await fetch_stock_quote("sh600000")
            assert result.stock_code == "sh600000"
            assert result.name == "浦发银行"
            mock_provider.get.assert_called_once_with("sh600000")

    @pytest.mark.asyncio
    async def test_fetch_quote_with_timeout(self) -> None:
        """测试带超时参数的股票行情获取。"""
        mock_quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.5,
            change=0.5,
            change_percent=5.0,
        )

        with patch("pocket_stock.cli.web.TencentStockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            # 正确设置 async context manager
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get = AsyncMock(return_value=mock_quote)

            result = await fetch_stock_quote("sh600000", timeout=15.0)
            assert result.stock_code == "sh600000"
            # 验证 Provider 被调用
            mock_provider_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_quote_network_error(self) -> None:
        """测试网络错误。"""
        with patch("pocket_stock.cli.web.TencentStockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            # 需要正确设置 async context manager
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get = AsyncMock(side_effect=NetworkError("sh600000", "Connection failed"))

            with pytest.raises(NetworkError):
                await fetch_stock_quote("sh600000")

    @pytest.mark.asyncio
    async def test_fetch_quote_service_error(self) -> None:
        """测试服务错误。"""
        with patch("pocket_stock.cli.web.TencentStockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            # 需要正确设置 async context manager
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get = AsyncMock(side_effect=ProviderServiceError("sh600000", 500, "Server error"))

            with pytest.raises(ProviderServiceError):
                await fetch_stock_quote("sh600000")


class TestSearchStockNews:
    """新闻搜索测试类。"""

    @pytest.mark.asyncio
    async def test_search_news_success(self) -> None:
        """测试成功搜索新闻。"""
        mock_response = MagicMock()
        mock_response.total_results = 10
        mock_response.dimension_count = 3
        mock_response.total_time = 1.5
        mock_response.dimensions = {}

        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.search_stock = AsyncMock(return_value=mock_response)
            mock_service_class.return_value = mock_service

            with patch("pocket_stock.cli.web.SearchConfigManager") as mock_config_manager_class:
                mock_config_manager = MagicMock()
                mock_user_config = MagicMock()
                mock_user_config.max_results = 5
                mock_user_config.search_depth = "basic"
                mock_user_config.chunks_per_source = 3
                mock_user_config.topic = "general"
                mock_user_config.include_answer = False
                mock_user_config.include_answer_level = None
                mock_user_config.country = "china"
                mock_config_manager.load.return_value = mock_user_config
                mock_config_manager_class.return_value = mock_config_manager

                result = await search_stock_news("浦发银行")
                assert result.total_results == 10
                # 验证 search_stock 被调用，现在会传递 SearchOptions 对象
                assert mock_service.search_stock.called
                call_args = mock_service.search_stock.call_args
                assert call_args[0][0] == "浦发银行"
                assert call_args[0][1] is not None  # SearchOptions 对象

    @pytest.mark.asyncio
    async def test_search_network_error(self) -> None:
        """测试搜索网络错误。"""
        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.search_stock = AsyncMock(side_effect=SearchNetworkError(message="Network error"))
            mock_service_class.return_value = mock_service

            with pytest.raises(SearchNetworkError):
                await search_stock_news("浦发银行")

    @pytest.mark.asyncio
    async def test_search_rate_limit_error(self) -> None:
        """测试搜索速率限制错误。"""
        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.search_stock = AsyncMock(side_effect=RateLimitError(limit="100 requests per minute"))
            mock_service_class.return_value = mock_service

            with pytest.raises(RateLimitError):
                await search_stock_news("浦发银行")


class TestAnalyseStockWithLLM:
    """LLM 股票分析测试类。"""

    def test_analyse_success(self) -> None:
        """测试成功分析股票。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.5,
            change=0.5,
            change_percent=5.0,
        )

        search_response = MagicMock()
        search_response.total_results = 10

        mock_result = StockAnalysisResult(
            stock_name="浦发银行",
            conclusion="股价上涨趋势明显，短期看多。",
            position_suggestion=PositionSuggestion(
                no_position="建议逢低买入，目标价12元。",
                has_position="建议继续持有，目标价12元。",
            ),
            target_prices=TargetPrices(buy_price=11.0, stop_loss_price=10.0, target_price=12.0),
            checklist=[
                ChecklistItem(content="技术面支撑", status="✅"),
                ChecklistItem(content="基本面良好", status="✅"),
                ChecklistItem(content="资金流向积极", status="⚠️"),
                ChecklistItem(content="风险可控", status="✅"),
                ChecklistItem(content="预期收益可观", status="✅"),
            ],
        )

        with patch("pocket_stock.cli.web.LLMStockAnalyser") as mock_analyser_class:
            mock_analyser = MagicMock()
            mock_analyser.analyse = MagicMock(return_value=mock_result)
            mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

            result = analyse_stock_with_llm(quote, search_response)
            assert result.conclusion == "股价上涨趋势明显，短期看多。"
            mock_analyser.analyse.assert_called_once_with(quote, search_response)

    def test_analyse_timeout_error(self) -> None:
        """测试 LLM 超时错误。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.5,
            change=0.5,
            change_percent=5.0,
        )

        search_response = MagicMock()

        with patch("pocket_stock.cli.web.LLMStockAnalyser") as mock_analyser_class:
            mock_analyser = MagicMock()
            mock_analyser.analyse = MagicMock(side_effect=LLMApiTimeoutError())
            mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

            with pytest.raises(LLMApiTimeoutError):
                analyse_stock_with_llm(quote, search_response)

    def test_analyse_auth_error(self) -> None:
        """测试 LLM 认证错误。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.5,
            change=0.5,
            change_percent=5.0,
        )

        search_response = MagicMock()

        with patch("pocket_stock.cli.web.LLMStockAnalyser") as mock_analyser_class:
            mock_analyser = MagicMock()
            mock_analyser.analyse = MagicMock(side_effect=LLMAuthenticationError())
            mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

            with pytest.raises(LLMAuthenticationError):
                analyse_stock_with_llm(quote, search_response)


class TestRenderStockQuote:
    """股票行情渲染测试类。"""

    @patch("pocket_stock.cli.web.st")
    def test_render_stock_quote_basic(self, mock_st) -> None:
        """测试基本股票行情渲染。"""
        quote = StockQuote(
            stock_code="sh600000",
            name="浦发银行",
            current_price=10.5,
            change=0.5,
            change_percent=5.0,
        )

        # Mock streamlit components
        mock_st.subheader = MagicMock()
        mock_st.columns = MagicMock(
            side_effect=[
                [MagicMock(), MagicMock(), MagicMock(), MagicMock()],  # 主行
                [MagicMock(), MagicMock(), MagicMock()],  # 详细信息行
            ]
        )
        mock_st.metric = MagicMock()
        mock_st.expander = MagicMock()
        mock_st.write = MagicMock()
        mock_st.divider = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.link_button = MagicMock()

        # Setup expander context manager
        mock_expander = MagicMock()
        mock_expander.__enter__ = MagicMock(return_value=mock_expander)
        mock_expander.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value = mock_expander

        # Setup main column mocks
        main_cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        main_cols[0].metric = MagicMock()
        main_cols[1].metric = MagicMock()
        main_cols[2].metric = MagicMock()
        main_cols[3].metric = MagicMock()

        # Setup detail column mocks
        detail_cols = [MagicMock(), MagicMock(), MagicMock()]
        detail_cols[0].write = MagicMock()
        detail_cols[1].write = MagicMock()
        detail_cols[2].write = MagicMock()

        mock_st.columns.side_effect = [main_cols, detail_cols]

        render_stock_quote(quote)

        # 验证关键调用
        mock_st.subheader.assert_called_once()
        assert mock_st.columns.call_count >= 2


class TestRenderSearchResults:
    """搜索结果渲染测试类。"""

    @patch("pocket_stock.cli.web.st")
    def test_render_search_results_basic(self, mock_st) -> None:
        """测试基本搜索结果渲染。"""
        mock_response = MagicMock()
        mock_response.total_results = 10
        mock_response.dimension_count = 3
        mock_response.total_time = 1.5
        mock_response.dimensions = {}

        # Mock streamlit components
        mock_st.subheader = MagicMock()
        mock_st.expander = MagicMock()
        mock_st.info = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.divider = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.success = MagicMock()

        # Setup expander context manager
        mock_expander = MagicMock()
        mock_expander.__enter__ = MagicMock(return_value=mock_expander)
        mock_expander.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value = mock_expander

        render_search_results(mock_response)

        mock_st.subheader.assert_called_once()


class TestRenderAnalysisResult:
    """分析结果渲染测试类。"""

    @patch("pocket_stock.cli.web.st")
    def test_render_analysis_result_basic(self, mock_st) -> None:
        """测试基本分析结果渲染。"""

        result = StockAnalysisResult(
            stock_name="浦发银行",
            conclusion="股价上涨趋势明显。",
            position_suggestion=PositionSuggestion(
                no_position="建议逢低买入。",
                has_position="建议继续持有。",
            ),
            target_prices=TargetPrices(buy_price=11.0, stop_loss_price=10.0, target_price=12.0),
            checklist=[
                ChecklistItem(content="技术面支撑", status="✅"),
                ChecklistItem(content="基本面良好", status="✅"),
                ChecklistItem(content="资金流向积极", status="⚠️"),
                ChecklistItem(content="风险可控", status="✅"),
                ChecklistItem(content="预期收益可观", status="✅"),
            ],
        )

        # Mock streamlit components
        mock_st.subheader = MagicMock()
        mock_st.info = MagicMock()
        mock_st.success = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.divider = MagicMock()
        mock_st.warning = MagicMock()

        # Setup column mocks - 需要3次调用:持仓建议(2列)、具体狙击点位(3列)
        position_cols = [MagicMock(), MagicMock()]
        price_cols = [MagicMock(), MagicMock(), MagicMock()]

        position_cols[0].success = MagicMock()
        position_cols[0].markdown = MagicMock()
        position_cols[1].success = MagicMock()
        position_cols[1].markdown = MagicMock()

        price_cols[0].metric = MagicMock()
        price_cols[1].metric = MagicMock()
        price_cols[2].metric = MagicMock()

        mock_st.columns.side_effect = [position_cols, price_cols]

        render_analysis_result(result)

        mock_st.subheader.assert_called_once()
        mock_st.info.assert_called_once()
        mock_st.success.assert_called()


class TestValidateDateRange:
    """日期范围验证测试类。"""

    def test_valid_date_range(self) -> None:
        """测试有效的日期范围。"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        with patch("pocket_stock.cli.web.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 10)

            # 需要重新导入函数以使用 mock
            from pocket_stock.cli.web import _validate_date_range

            is_valid, error = _validate_date_range(start_date, end_date)
            assert is_valid is True
            assert error is None

    def test_invalid_date_range_start_after_end(self) -> None:
        """测试无效的日期范围（起始时间晚于结束时间）。"""
        start_date = date(2024, 1, 10)
        end_date = date(2024, 1, 1)

        with patch("pocket_stock.cli.web.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)

            from pocket_stock.cli.web import _validate_date_range

            is_valid, error = _validate_date_range(start_date, end_date)
            assert is_valid is False
            assert error == "起始时间不能晚于结束时间"

    def test_invalid_date_range_end_after_today(self) -> None:
        """测试无效的日期范围（结束时间晚于今天）。"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        with patch("pocket_stock.cli.web.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 10)

            from pocket_stock.cli.web import _validate_date_range

            is_valid, error = _validate_date_range(start_date, end_date)
            assert is_valid is False
            assert error == "结束时间不能晚于今天"

    def test_equal_dates(self) -> None:
        """测试起始日期和结束日期相同的情况。"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)

        with patch("pocket_stock.cli.web.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 5)

            from pocket_stock.cli.web import _validate_date_range

            is_valid, error = _validate_date_range(start_date, end_date)
            assert is_valid is True
            assert error is None

    def test_date_range_today(self) -> None:
        """测试结束日期为今天的情况。"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 10)

        with patch("pocket_stock.cli.web.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 10)

            from pocket_stock.cli.web import _validate_date_range

            is_valid, error = _validate_date_range(start_date, end_date)
            assert is_valid is True
            assert error is None


class TestGetNewsDateRange:
    """获取新闻日期范围测试类。"""

    @patch("pocket_stock.cli.web.st")
    def test_get_date_range_from_session_state(self, mock_st) -> None:
        """测试从 session state 获取日期范围。"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        mock_st.session_state.news_date_start = start_date
        mock_st.session_state.news_date_end = end_date

        from pocket_stock.cli.web import _get_news_date_range

        result_start, result_end = _get_news_date_range()
        assert result_start == start_date
        assert result_end == end_date


class TestSetNewsDateRange:
    """设置新闻日期范围测试类。"""

    @patch("pocket_stock.cli.web.st")
    def test_set_date_range_to_session_state(self, mock_st) -> None:
        """测试设置日期范围到 session state。"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        # 使用 MagicMock 而不是空字典，这样可以设置属性
        mock_st.session_state = MagicMock()

        from pocket_stock.cli.web import _set_news_date_range

        _set_news_date_range(start_date, end_date)
        assert mock_st.session_state.news_date_start == start_date
        assert mock_st.session_state.news_date_end == end_date


class TestSearchStockNewsWithDateRange:
    """带日期范围的新闻搜索测试类。"""

    @pytest.mark.asyncio
    async def test_search_news_with_date_range(self) -> None:
        """测试带日期范围的成功搜索。"""
        from pocket_stock.search.models import SearchOptions

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)

        mock_response = MagicMock()
        mock_response.total_results = 10
        mock_response.dimension_count = 3
        mock_response.total_time = 1.5
        mock_response.dimensions = {}

        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            with patch("pocket_stock.cli.web.SearchConfigManager") as mock_config_manager_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_response)
                mock_service_class.return_value = mock_service

                mock_config_manager = MagicMock()
                mock_user_config = MagicMock()
                mock_user_config.max_results = 5
                mock_user_config.search_depth = "basic"
                mock_user_config.chunks_per_source = 3
                mock_user_config.topic = "general"
                mock_user_config.include_answer = False
                mock_user_config.include_answer_level = None
                mock_user_config.country = "china"
                mock_config_manager.load.return_value = mock_user_config
                mock_config_manager_class.return_value = mock_config_manager

                result = await search_stock_news("浦发银行", start_date, end_date)
                assert result.total_results == 10
                assert mock_service.search_stock.called
                call_args = mock_service.search_stock.call_args
                assert call_args[0][0] == "浦发银行"
                assert isinstance(call_args[0][1], SearchOptions)
                assert call_args[0][1].start_date == start_date.isoformat()
                assert call_args[0][1].end_date == end_date.isoformat()

    @pytest.mark.asyncio
    async def test_search_news_with_only_start_date(self) -> None:
        """测试只有起始日期的新闻搜索。"""
        from pocket_stock.search.models import SearchOptions

        start_date = date(2024, 1, 1)

        mock_response = MagicMock()
        mock_response.total_results = 10
        mock_response.dimension_count = 3
        mock_response.total_time = 1.5
        mock_response.dimensions = {}

        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            with patch("pocket_stock.cli.web.SearchConfigManager") as mock_config_manager_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_response)
                mock_service_class.return_value = mock_service

                mock_config_manager = MagicMock()
                mock_user_config = MagicMock()
                mock_user_config.max_results = 5
                mock_user_config.search_depth = "basic"
                mock_user_config.chunks_per_source = 3
                mock_user_config.topic = "general"
                mock_user_config.include_answer = False
                mock_user_config.include_answer_level = None
                mock_user_config.country = "china"
                mock_config_manager.load.return_value = mock_user_config
                mock_config_manager_class.return_value = mock_config_manager

                result = await search_stock_news("浦发银行", start_date, None)
                assert result.total_results == 10
                assert mock_service.search_stock.called
                call_args = mock_service.search_stock.call_args
                assert call_args[0][0] == "浦发银行"
                assert isinstance(call_args[0][1], SearchOptions)
                assert call_args[0][1].start_date == start_date.isoformat()
                assert call_args[0][1].end_date is None

    @pytest.mark.asyncio
    async def test_search_news_with_only_end_date(self) -> None:
        """测试只有结束日期的新闻搜索。"""
        from pocket_stock.search.models import SearchOptions

        end_date = date(2024, 1, 7)

        mock_response = MagicMock()
        mock_response.total_results = 10
        mock_response.dimension_count = 3
        mock_response.total_time = 1.5
        mock_response.dimensions = {}

        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            with patch("pocket_stock.cli.web.SearchConfigManager") as mock_config_manager_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_response)
                mock_service_class.return_value = mock_service

                mock_config_manager = MagicMock()
                mock_user_config = MagicMock()
                mock_user_config.max_results = 5
                mock_user_config.search_depth = "basic"
                mock_user_config.chunks_per_source = 3
                mock_user_config.topic = "general"
                mock_user_config.include_answer = False
                mock_user_config.include_answer_level = None
                mock_user_config.country = "china"
                mock_config_manager.load.return_value = mock_user_config
                mock_config_manager_class.return_value = mock_config_manager

                result = await search_stock_news("浦发银行", None, end_date)
                assert result.total_results == 10
                assert mock_service.search_stock.called
                call_args = mock_service.search_stock.call_args
                assert call_args[0][0] == "浦发银行"
                assert isinstance(call_args[0][1], SearchOptions)
                assert call_args[0][1].start_date is None
                assert call_args[0][1].end_date == end_date.isoformat()

    @pytest.mark.asyncio
    async def test_search_news_without_date_range(self) -> None:
        """测试不带日期范围的新闻搜索。"""
        from pocket_stock.search.models import SearchOptions

        mock_response = MagicMock()
        mock_response.total_results = 10
        mock_response.dimension_count = 3
        mock_response.total_time = 1.5
        mock_response.dimensions = {}

        with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
            with patch("pocket_stock.cli.web.SearchConfigManager") as mock_config_manager_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_response)
                mock_service_class.return_value = mock_service

                mock_config_manager = MagicMock()
                mock_user_config = MagicMock()
                mock_user_config.max_results = 5
                mock_user_config.search_depth = "basic"
                mock_user_config.chunks_per_source = 3
                mock_user_config.topic = "general"
                mock_user_config.include_answer = False
                mock_user_config.include_answer_level = None
                mock_user_config.country = "china"
                mock_config_manager.load.return_value = mock_user_config
                mock_config_manager_class.return_value = mock_config_manager

                result = await search_stock_news("浦发银行")
                assert result.total_results == 10
                assert mock_service.search_stock.called
                call_args = mock_service.search_stock.call_args
                assert call_args[0][0] == "浦发银行"
                # 即使没有日期范围，也会传递 SearchOptions 对象（而不是 None）
                assert isinstance(call_args[0][1], SearchOptions)
                assert call_args[0][1].start_date is None
                assert call_args[0][1].end_date is None

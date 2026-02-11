"""Web 模块集成测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pocket_stock.cli.web import (
    analyse_stock_with_llm,
    fetch_stock_quote,
    search_stock_news,
    validate_stock_code,
)
from pocket_stock.llm.models import ChecklistItem


class TestWebIntegration:
    """Web 模块集成测试类。"""

    @pytest.mark.asyncio
    async def test_complete_analysis_flow(self) -> None:
        """测试完整的股票分析流程。"""
        from pocket_stock.llm import StockAnalysisResult, TargetPrices
        from pocket_stock.llm.models import PositionSuggestion

        # Mock 股票行情数据
        mock_quote = MagicMock()
        mock_quote.stock_code = "sh600000"
        mock_quote.name = "浦发银行"
        mock_quote.current_price = 10.5
        mock_quote.change = 0.5
        mock_quote.change_percent = 5.0
        mock_quote.open_price = 10.3
        mock_quote.close_price = 10.4
        mock_quote.high_price = 10.6
        mock_quote.low_price = 10.2
        mock_quote.volume = 150000
        mock_quote.turnover = 1575000.0

        # Mock 搜索响应
        mock_search_response = MagicMock()
        mock_search_response.total_results = 10
        mock_search_response.dimension_count = 3
        mock_search_response.total_time = 1.5

        # Mock 搜索维度结果
        mock_dimension = MagicMock()
        mock_dimension.result_count = 5
        mock_dimension.results = []

        mock_dimension_result = MagicMock()
        mock_dimension_result.title = "浦发银行发布年报"
        mock_dimension_result.url = "https://example.com/news/1"
        mock_dimension_result.content = "浦发银行发布2023年度报告..."

        mock_dimension.results = [mock_dimension_result]
        mock_search_response.dimensions = {"latest_news": mock_dimension}

        # Mock LLM 分析结果
        mock_analysis_result = MagicMock()
        mock_analysis_result.conclusion = "股价上涨趋势明显，短期看多。"
        mock_analysis_result.position_suggestion = MagicMock()
        mock_analysis_result.position_suggestion.no_position = "建议逢低买入，目标价12元。"
        mock_analysis_result.position_suggestion.has_position = "建议继续持有，目标价12元。"
        mock_analysis_result.target_prices = MagicMock()
        mock_analysis_result.target_prices.buy_price = 11.0
        mock_analysis_result.target_prices.stop_loss_price = 10.0
        mock_analysis_result.target_prices.target_price = 12.0
        mock_analysis_result.checklist = []

        # 1. 验证股票代码
        is_valid, error = validate_stock_code("sh600000")
        assert is_valid is True
        assert error is None

        # 2. 获取股票行情
        with patch("pocket_stock.cli.web.StockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get_stock_quote = AsyncMock(return_value=mock_quote)

            quote = await fetch_stock_quote("sh600000")
            assert quote.stock_code == "sh600000"
            assert quote.name == "浦发银行"

            # 3. 搜索相关新闻
            with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_search_response)
                mock_service_class.return_value = mock_service

                search_response = await search_stock_news("浦发银行")
                assert search_response.total_results == 10

                # 4. LLM 分析 - 创建正确的 StockAnalysisResult
                result = StockAnalysisResult(
                    stock_name="浦发银行",
                    conclusion="股价上涨趋势明显，短期看多。",
                    position_suggestion=PositionSuggestion(
                        no_position="建议逢低买入，目标价12元。",
                        has_position="建议继续持有，目标价12元。",
                    ),
                    target_prices=TargetPrices(
                        buy_price=11.0, stop_loss_price=10.0, target_price=12.0
                    ),
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
                    mock_analyser.analyse = MagicMock(return_value=result)
                    mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

                    analysis_result = analyse_stock_with_llm(quote, search_response)
                    assert analysis_result.conclusion == "股价上涨趋势明显，短期看多。"

    @pytest.mark.asyncio
    async def test_analysis_flow_with_network_error(self) -> None:
        """测试网络错误情况下的分析流程。"""
        from pocket_stock.data_provider.exceptions import NetworkErrorException

        with patch("pocket_stock.cli.web.StockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get_stock_quote = AsyncMock(
                side_effect=NetworkErrorException(stock_code="sh600000", reason="Connection timeout")
            )

            with pytest.raises(NetworkErrorException) as exc_info:
                await fetch_stock_quote("sh600000")

            assert "Connection timeout" in str(exc_info.value.reason)

    @pytest.mark.asyncio
    async def test_analysis_flow_with_search_error(self) -> None:
        """测试搜索服务错误情况下的分析流程。"""
        from pocket_stock.data_provider.exceptions import NetworkErrorException
        from pocket_stock.search.exceptions import RateLimitError

        # Mock 股票行情数据
        mock_quote = MagicMock()
        mock_quote.stock_code = "sh600000"
        mock_quote.name = "浦发银行"
        mock_quote.current_price = 10.5
        mock_quote.change = 0.5
        mock_quote.change_percent = 5.0

        # 1. 获取股票行情成功
        with patch("pocket_stock.cli.web.StockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get_stock_quote = AsyncMock(return_value=mock_quote)

            quote = await fetch_stock_quote("sh600000")
            assert quote.stock_code == "sh600000"

            # 2. 搜索新闻失败
            with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(
                    side_effect=RateLimitError(limit="100 requests per minute")
                )
                mock_service_class.return_value = mock_service

                with pytest.raises(RateLimitError) as exc_info:
                    await search_stock_news("浦发银行")

                assert "100 requests per minute" in str(exc_info.value.limit)

    @pytest.mark.asyncio
    async def test_analysis_flow_with_llm_error(self) -> None:
        """测试 LLM 分析错误情况下的分析流程。"""
        from pocket_stock.llm import LLMApiTimeoutError

        # Mock 股票行情数据
        mock_quote = MagicMock()
        mock_quote.stock_code = "sh600000"
        mock_quote.name = "浦发银行"
        mock_quote.current_price = 10.5
        mock_quote.change = 0.5
        mock_quote.change_percent = 5.0

        # Mock 搜索响应
        mock_search_response = MagicMock()
        mock_search_response.total_results = 10
        mock_search_response.dimension_count = 3
        mock_search_response.total_time = 1.5
        mock_search_response.dimensions = {}

        # 1. 获取股票行情成功
        with patch("pocket_stock.cli.web.StockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get_stock_quote = AsyncMock(return_value=mock_quote)

            quote = await fetch_stock_quote("sh600000")

            # 2. 搜索新闻成功
            with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_search_response)
                mock_service_class.return_value = mock_service

                search_response = await search_stock_news("浦发银行")

                # 3. LLM 分析失败
                with patch("pocket_stock.cli.web.LLMStockAnalyser") as mock_analyser_class:
                    mock_analyser = MagicMock()
                    mock_analyser.analyse = MagicMock(
                        side_effect=LLMApiTimeoutError()
                    )
                    mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

                    with pytest.raises(LLMApiTimeoutError):
                        analyse_stock_with_llm(quote, search_response)

    @pytest.mark.asyncio
    async def test_multiple_stock_codes_analysis(self) -> None:
        """测试多个股票代码的顺序分析。"""
        from pocket_stock.llm import StockAnalysisResult, TargetPrices
        from pocket_stock.llm.models import PositionSuggestion

        stock_codes = ["sh600000", "sz000001"]

        # Mock 数据
        mock_quote_1 = MagicMock()
        mock_quote_1.stock_code = "sh600000"
        mock_quote_1.name = "浦发银行"
        mock_quote_1.current_price = 10.5

        mock_quote_2 = MagicMock()
        mock_quote_2.stock_code = "sz000001"
        mock_quote_2.name = "平安银行"
        mock_quote_2.current_price = 12.5

        mock_search_response = MagicMock()
        mock_search_response.total_results = 5
        mock_search_response.dimension_count = 2
        mock_search_response.total_time = 1.0
        mock_search_response.dimensions = {}

        mock_analysis_result = MagicMock()
        mock_analysis_result.conclusion = "分析结论"
        mock_analysis_result.position_suggestion = MagicMock()
        mock_analysis_result.position_suggestion.no_position = "空仓建议"
        mock_analysis_result.position_suggestion.has_position = "持仓建议"
        mock_analysis_result.target_prices = MagicMock()
        mock_analysis_result.target_prices.buy_price = 11.0
        mock_analysis_result.target_prices.stop_loss_price = 10.0
        mock_analysis_result.target_prices.target_price = 12.0
        mock_analysis_result.checklist = []

        with patch("pocket_stock.cli.web.StockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get_stock_quote = AsyncMock(side_effect=[mock_quote_1, mock_quote_2])

            with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_search_response)
                mock_service_class.return_value = mock_service

                result = StockAnalysisResult(
                    stock_name="浦发银行",
                    conclusion="分析结论",
                    position_suggestion=PositionSuggestion(
                        no_position="空仓建议", has_position="持仓建议"
                    ),
                    target_prices=TargetPrices(
                        buy_price=11.0, stop_loss_price=10.0, target_price=12.0
                    ),
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
                    mock_analyser.analyse = MagicMock(return_value=result)
                    mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

                    results = []
                    for code in stock_codes:
                        is_valid, error = validate_stock_code(code)
                        assert is_valid is True

                        quote = await fetch_stock_quote(code)
                        search_response = await search_stock_news(quote.name)
                        analysis_result = analyse_stock_with_llm(quote, search_response)

                        results.append((quote, search_response, analysis_result))

                    assert len(results) == 2
                    assert results[0][0].stock_code == "sh600000"
                    assert results[1][0].stock_code == "sz000001"

    @pytest.mark.asyncio
    async def test_empty_search_results_handling(self) -> None:
        """测试空搜索结果的处理。"""
        from pocket_stock.llm import StockAnalysisResult, TargetPrices
        from pocket_stock.llm.models import PositionSuggestion

        # Mock 股票行情数据
        mock_quote = MagicMock()
        mock_quote.stock_code = "sh600000"
        mock_quote.name = "浦发银行"
        mock_quote.current_price = 10.5
        mock_quote.change = 0.5
        mock_quote.change_percent = 5.0

        # Mock 空搜索响应
        mock_search_response = MagicMock()
        mock_search_response.total_results = 0
        mock_search_response.dimension_count = 0
        mock_search_response.total_time = 0.5
        mock_search_response.dimensions = {}

        mock_analysis_result = MagicMock()
        mock_analysis_result.conclusion = "无新闻数据，基于价格走势分析。"
        mock_analysis_result.position_suggestion = MagicMock()
        mock_analysis_result.position_suggestion.no_position = "建议观望"
        mock_analysis_result.position_suggestion.has_position = "建议持有"
        mock_analysis_result.target_prices = MagicMock()
        mock_analysis_result.target_prices.buy_price = 10.8
        mock_analysis_result.target_prices.stop_loss_price = 10.0
        mock_analysis_result.target_prices.target_price = 11.5
        mock_analysis_result.checklist = []

        with patch("pocket_stock.cli.web.StockDataProvider") as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider_class.return_value.__aenter__.return_value = mock_provider
            mock_provider_class.return_value.__aexit__.return_value = None
            mock_provider.get_stock_quote = AsyncMock(return_value=mock_quote)

            quote = await fetch_stock_quote("sh600000")

            with patch("pocket_stock.cli.web.SearchService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.search_stock = AsyncMock(return_value=mock_search_response)
                mock_service_class.return_value = mock_service

                search_response = await search_stock_news("浦发银行")
                assert search_response.total_results == 0
                assert search_response.dimension_count == 0

                result = StockAnalysisResult(
                    stock_name="浦发银行",
                    conclusion="无新闻数据，基于价格走势分析。",
                    position_suggestion=PositionSuggestion(
                        no_position="建议观望", has_position="建议持有"
                    ),
                    target_prices=TargetPrices(
                        buy_price=10.8, stop_loss_price=10.0, target_price=11.5
                    ),
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
                    mock_analyser.analyse = MagicMock(return_value=result)
                    mock_analyser_class.from_env = MagicMock(return_value=mock_analyser)

                    analysis_result = analyse_stock_with_llm(quote, search_response)
                    assert analysis_result.conclusion == "无新闻数据，基于价格走势分析。"

"""股票分析 Web 应用。

这是一个基于 Streamlit 的极简股票分析 Web 界面，提供股票行情查询、新闻搜索和 AI 智能分析功能。
"""

from __future__ import annotations

import asyncio
import re
from datetime import date, datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    DataParseError,
    DataValidationError,
    InvalidStockCodeError,
    NetworkError,
    ProviderServiceError,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.tencent.provider import TencentStockDataProvider
from pocket_stock.llm import (
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMServiceError,
    LLMStockAnalyser,
    NetworkConnectionError,
    StockAnalysisResult,
)
from pocket_stock.search.exceptions import (
    AuthenticationError as SearchAuthenticationError,
    ConfigurationError as SearchConfigurationError,
    MissingAPIKeyError as SearchMissingAPIKeyError,
    NetworkError as SearchNetworkError,
    RateLimitError,
    SearchError,
    ServiceError as SearchServiceError,
    ValidationError as SearchValidationError,
)
from pocket_stock.search.models import StockSearchDimension, StockSearchResponse
from pocket_stock.search.service import SearchService

# 加载 .env 文件
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="Pocket Stock - 股票分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def validate_stock_code(stock_code: str) -> tuple[bool, str | None]:
    """验证股票代码格式。

    Args:
        stock_code: 待验证的股票代码

    Returns:
        验证结果和错误消息 (是否有效, 错误消息)

    Examples:
        >>> is_valid, error = validate_stock_code("sh600000")
        >>> is_valid
        True
        >>> is_valid, error = validate_stock_code("123456")
        >>> is_valid
        False
    """
    if not stock_code:
        return False, "股票代码不能为空"

    stock_code = stock_code.strip().lower()

    # 检查格式：sh 或 sz 开头，后跟 6 位数字
    pattern = r"^(sh|sz)\d{6}$"
    if not re.match(pattern, stock_code):
        return False, "股票代码格式无效，请使用 sh600000 或 sz000001 格式"

    return True, None


async def fetch_stock_quote(stock_code: str, timeout: float = 10.0) -> StockQuote:
    """异步获取股票行情数据。

    Args:
        stock_code: 股票代码
        timeout: 超时时间（秒）

    Returns:
        股票行情数据对象

    Raises:
        InvalidStockCodeError: 股票代码无效
        NetworkError: 网络错误
        ProviderServiceError: 服务错误
    """
    config = ProviderConfig(timeout=timeout)
    async with TencentStockDataProvider(config) as provider:
        quote = await provider.get(stock_code)
    return quote


async def search_stock_news(
    stock_name: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> StockSearchResponse:
    """异步搜索指定股票的相关新闻。

    Args:
        stock_name: 股票名称
        start_date: 搜索起始日期，如果为 None 则不限制起始时间
        end_date: 搜索结束日期，如果为 None 则不限制结束时间

    Returns:
        搜索响应对象，包含各维度的搜索结果

    Raises:
        SearchError: 当搜索服务出现异常时抛出。
    """
    service = SearchService()

    # 构建搜索配置（使用默认 topic）
    search_config = None
    if start_date or end_date:
        from pocket_stock.search.models import SearchOptions

        config_dict = {}
        if start_date:
            config_dict["start_date"] = start_date.isoformat()
        if end_date:
            config_dict["end_date"] = end_date.isoformat()

        search_config = SearchOptions(**config_dict)

    response = await service.search_stock(stock_name, search_config)
    return response


def analyse_stock_with_llm(quote: StockQuote, search_response: StockSearchResponse) -> StockAnalysisResult:
    """使用 LLM 分析股票。

    Args:
        quote: 股票行情数据
        search_response: 搜索结果

    Returns:
        股票分析结果

    Raises:
        LLMApiTimeoutError: API 调用超时
        LLMAuthenticationError: API 认证失败
        LLMServiceError: 服务返回错误
        NetworkConnectionError: 网络连接错误
    """
    analyser = LLMStockAnalyser.from_env()
    result = analyser.analyse(quote, search_response)
    return result


def render_stock_quote(quote: StockQuote) -> None:
    """渲染股票行情数据。

    Args:
        quote: 股票行情数据对象
    """
    st.subheader("📊 股票行情")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("股票代码", quote.stock_code)

    with col2:
        st.metric("股票名称", quote.name)

    with col3:
        change_color = "normal" if quote.change >= 0 else "inverse"
        st.metric("当前价格", f"{quote.current_price:.2f} 元", delta=f"{quote.change:+.2f}", delta_color=change_color)

    with col4:
        change_percent_color = "normal" if quote.change_percent >= 0 else "inverse"
        st.metric(
            "涨跌幅",
            f"{quote.change_percent:+.2f}%",
            delta=f"{quote.change:+.2f} 元",
            delta_color=change_percent_color,
        )

    # 详细信息
    with st.expander("查看详细信息"):
        col1, col2, col3 = st.columns(3)

        with col1:
            if quote.open_price:
                st.write(f"**开盘价**: {quote.open_price:.2f} 元")
            if quote.close_price:
                st.write(f"**收盘价**: {quote.close_price:.2f} 元")

        with col2:
            if quote.high_price:
                st.write(f"**最高价**: {quote.high_price:.2f} 元")
            if quote.low_price:
                st.write(f"**最低价**: {quote.low_price:.2f} 元")

        with col3:
            volume_str = _format_volume(quote.volume)
            st.write(f"**成交量**: {volume_str}")
            turnover_str = _format_turnover(quote.turnover)
            st.write(f"**成交额**: {turnover_str}")

        if quote.timestamp:
            st.write(f"**更新时间**: {quote.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def render_search_results(response: StockSearchResponse, date_start: date | None = None, date_end: date | None = None) -> None:
    """渲染搜索结果。

    Args:
        response: 搜索响应对象
        date_start: 搜索起始日期，用于显示时间范围信息
        date_end: 搜索结束日期，用于显示时间范围信息
    """
    # 显示时间范围信息
    if date_start and date_end:
        st.info(f"📅 搜索时间范围: {date_start} 至 {date_end}")

    st.subheader("📰 相关新闻")

    dimension_names = {
        StockSearchDimension.LATEST_NEWS: "最新消息",
        StockSearchDimension.INSTITUTION_ANALYSIS: "机构分析",
        StockSearchDimension.RISK_ANALYSIS: "风险排查",
        StockSearchDimension.PERFORMANCE_EXPECTATION: "业绩预期",
        StockSearchDimension.INDUSTRY_ANALYSIS: "行业分析",
    }

    for dimension, search_response in response.dimensions.items():
        dimension_name = dimension_names.get(dimension, dimension.value)

        with st.expander(f"【{dimension_name}】({search_response.result_count} 条结果)", expanded=True):
            if search_response.results:
                for i, result in enumerate(search_response.results[:5], 1):
                    st.markdown(f"{i}. **{result.title}**")
                    st.markdown(f"   🔗 [查看原文]({result.url})")
                    if result.content:
                        preview = result.content[:150] + "..." if len(result.content) > 150 else result.content
                        st.caption(preview)
                    st.divider()
            else:
                st.info("暂无相关结果")

    st.caption(f"总结果数: {response.total_results} | 搜索维度: {response.dimension_count} | 耗时: {response.total_time:.2f}秒")


def render_analysis_result(result: StockAnalysisResult) -> None:
    """渲染 LLM 分析结果。

    Args:
        result: 股票分析结果对象
    """
    st.subheader("🤖 AI 智能分析")

    # 核心结论
    st.info("【核心结论】")
    st.markdown(result.conclusion)

    # 持仓分类建议
    col1, col2 = st.columns(2)
    with col1:
        st.success("【空仓者建议】")
        st.markdown(result.position_suggestion.no_position)

    with col2:
        st.success("【持仓者建议】")
        st.markdown(result.position_suggestion.has_position)

    # 具体狙击点位
    st.markdown("### 【具体狙击点位】")
    col1, col2, col3 = st.columns(3)
    with col1:
        buy_price = f"{result.target_prices.buy_price:.2f} 元" if result.target_prices.buy_price else "-"
        st.metric("💰 买入价", buy_price)
    with col2:
        stop_loss_price = f"{result.target_prices.stop_loss_price:.2f} 元" if result.target_prices.stop_loss_price else "-"
        st.metric("🛑 止损价", stop_loss_price)
    with col3:
        target_price = f"{result.target_prices.target_price:.2f} 元" if result.target_prices.target_price else "-"
        st.metric("🎯 目标价", target_price)

    # 检查清单
    st.markdown("### 【检查清单】")
    for item in result.checklist:
        icon = "✅" if item.status else "❌"
        st.markdown(f"{icon} {item.content}")


def format_error_message(e: Exception, stock_code: str | None = None) -> str:
    """格式化错误消息。

    Args:
        e: 异常对象
        stock_code: 股票代码（可选）

    Returns:
        友好的错误消息
    """
    code = stock_code if stock_code else "未知"

    if isinstance(e, InvalidStockCodeError):
        return f"股票代码格式无效\n\n股票代码: {code}\n提示: 格式应为 sh 或 sz 开头，后跟 6 位数字，如 sh600000"

    if isinstance(e, NetworkError):
        return f"网络连接失败\n\n股票代码: {e.stock_code}\n原因: {e.reason}"

    if isinstance(e, ProviderServiceError):
        return f"数据服务异常\n\n股票代码: {e.stock_code}\n状态码: {e.status_code}\n原因: {e.reason}"

    if isinstance(e, (DataParseError, DataValidationError)):
        detail = e.message if isinstance(e, DataValidationError) else e.detail
        return f"数据解析失败\n\n股票代码: {e.stock_code if isinstance(e, DataParseError) else code}\n详情: {detail}"

    if isinstance(e, SearchMissingAPIKeyError):
        return "搜索服务未配置 API Key\n\n提示: 请在 .env 文件中设置 TAVILY_API_KEY"

    if isinstance(e, SearchAuthenticationError):
        return "搜索服务 API 认证失败\n\n提示: 请检查 TAVILY_API_KEY 是否正确"

    if isinstance(e, RateLimitError):
        return f"搜索服务达到速率限制\n\n限制: {e.limit}"

    if isinstance(e, (SearchValidationError, SearchConfigurationError)):
        return f"搜索服务配置或参数错误 - {e.message}"

    if isinstance(e, (SearchNetworkError, SearchServiceError)):
        return f"搜索服务请求失败 - {e.message}"

    if isinstance(e, SearchError):
        return f"搜索服务异常 - {e.message}"

    if isinstance(e, LLMApiTimeoutError):
        return f"LLM API 调用超时\n\n详情: {e}"

    if isinstance(e, LLMAuthenticationError):
        return "LLM API 认证失败\n\n提示: 请检查 OPENAI_API_KEY 是否正确"

    if isinstance(e, NetworkConnectionError):
        return f"无法连接到 LLM 服务\n\n详情: {e}"

    if isinstance(e, LLMServiceError):
        return f"LLM 服务返回错误\n\n详情: {e}"

    return f"发生未知错误\n\n股票代码: {code}\n异常类型: {type(e).__name__}\n异常信息: {e}"


def _format_volume(volume: int | None) -> str:
    """格式化成交量。

    Args:
        volume: 成交量（股）

    Returns:
        格式化后的字符串，自动转换单位
    """
    if volume is None or volume == 0:
        return "0"

    if volume >= 100000000:
        return f"{volume / 100000000:.2f} 亿股"
    elif volume >= 10000:
        return f"{volume / 10000:.2f} 万股"
    else:
        return f"{volume} 股"


def _format_turnover(turnover: float | None) -> str:
    """格式化成交额。

    Args:
        turnover: 成交额（元）

    Returns:
        格式化后的字符串，自动转换单位
    """
    if turnover is None or turnover == 0:
        return "0 元"

    if turnover >= 100000000:
        return f"{turnover / 100000000:.2f} 亿元"
    elif turnover >= 10000:
        return f"{turnover / 10000:.2f} 万元"
    else:
        return f"{turnover:.2f} 元"


def _init_news_date_range() -> None:
    """初始化新闻搜索时间范围的 session state。

    设置默认起始时间为一周前，结束时间为今天。
    如果 session state 中已存在这些键，则保持不变。
    当检测到页面刷新时（通过检查 page_refreshed 标记），重置时间范围为默认值。
    """
    today = date.today()
    week_ago = today - timedelta(days=7)

    # 检测页面刷新：如果 page_refreshed 标记存在且为 True，则表示是刷新
    if st.session_state.get("page_refreshed", False):
        # 重置时间范围为默认值
        st.session_state.news_date_start = week_ago
        st.session_state.news_date_end = today
        # 重置刷新标记
        st.session_state.page_refreshed = False
    else:
        # 首次加载，初始化时间范围
        if "news_date_start" not in st.session_state:
            st.session_state.news_date_start = week_ago
        if "news_date_end" not in st.session_state:
            st.session_state.news_date_end = today

    # 设置刷新标记为 True，下次运行时如果标记仍为 True，说明页面被刷新了
    st.session_state.page_refreshed = True


def _get_news_date_range() -> tuple[date, date]:
    """获取当前选择的新闻搜索时间范围。

    Returns:
        元组 (起始日期, 结束日期)
    """
    return st.session_state.news_date_start, st.session_state.news_date_end


def _set_news_date_range(start_date: date, end_date: date) -> None:
    """设置新闻搜索时间范围。

    Args:
        start_date: 起始日期
        end_date: 结束日期
    """
    st.session_state.news_date_start = start_date
    st.session_state.news_date_end = end_date


def _validate_date_range(start_date: date, end_date: date) -> tuple[bool, str | None]:
    """验证时间范围的有效性。

    Args:
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        元组 (是否有效, 错误消息)
    """
    if start_date > end_date:
        return False, "起始时间不能晚于结束时间"

    if end_date > date.today():
        return False, "结束时间不能晚于今天"

    return True, None


def render_settings_page() -> None:
    """渲染设置页面。

    该函数负责显示设置页面的内容。
    """
    st.title("⚙️ 设置")
    st.info("设置页面功能正在开发中...")


def render_home_page() -> None:
    """渲染主页 - 股票分析功能。

    该函数负责处理用户输入并展示分析结果，包括股票行情、新闻和AI分析。
    """
    st.title("📈 Pocket Stock - 股票分析")
    st.markdown("输入股票代码，获取实时行情、相关新闻和 AI 智能分析")

    # 初始化 session state
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None

    # 初始化时间范围状态
    _init_news_date_range()

    # 股票代码输入
    stock_code = st.text_input(
        "股票代码",
        placeholder="格式: sh600000 或 sz000001",
        help="请输入股票代码，如 sh600000（上海）或 sz000001（深圳）",
        key="stock_code_input",
    ).strip()

    # 时间范围选择组件
    st.divider()
    st.markdown("### 📅 新闻搜索时间范围")

    current_start, current_end = _get_news_date_range()

    date_range = st.date_input(
        "选择时间范围",
        value=(current_start, current_end),
        format="YYYY-MM-DD",
        key="news_date_range_input",
        help="选择搜索新闻的时间区间，系统将只搜索该时间段内的相关新闻",
    )

    # 更新时间范围到 session state
    if isinstance(date_range, tuple) and len(date_range) == 2:
        new_start, new_end = date_range
        # 只有当值真正改变时才更新，避免不必要的重绘
        if new_start != current_start or new_end != current_end:
            _set_news_date_range(new_start, new_end)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)

    # 执行分析
    if analyze_button:
        # 验证输入
        is_valid, error_msg = validate_stock_code(stock_code)
        if not is_valid:
            st.error(error_msg)
            st.stop()

        # 验证时间范围
        date_start, date_end = _get_news_date_range()
        is_date_valid, date_error_msg = _validate_date_range(date_start, date_end)
        if not is_date_valid:
            st.error(date_error_msg)
            st.stop()

        # 显示加载状态
        with st.spinner("正在分析中，请稍候..."):
            try:
                # 获取股票行情
                quote = asyncio.run(fetch_stock_quote(stock_code))

                # 获取时间范围
                date_start, date_end = _get_news_date_range()

                # 搜索相关新闻（传入时间范围）
                search_response = asyncio.run(search_stock_news(quote.name, date_start, date_end))

                # LLM 分析
                analysis_result = analyse_stock_with_llm(quote, search_response)

                # 保存结果到 session state
                st.session_state.quote = quote
                st.session_state.search_response = search_response
                st.session_state.analysis_result = analysis_result
                st.session_state.analysis_complete = True
                st.session_state.error_message = None

            except Exception as e:
                st.session_state.error_message = format_error_message(e, stock_code)
                st.session_state.analysis_complete = False

    # 显示错误信息
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        if st.button("🔄 重试", key="retry_button"):
            st.session_state.error_message = None
            st.rerun()

        # 显示分析结果
        if st.session_state.analysis_complete and st.session_state.get("quote"):
            quote = st.session_state.quote
            search_response = st.session_state.search_response
            analysis_result = st.session_state.analysis_result

            # 获取时间范围
            date_start, date_end = _get_news_date_range()

            # 使用 Tab 组织内容
            tab1, tab2, tab3 = st.tabs(["📊 行情", "📰 新闻", "🤖 AI 分析"])

            with tab1:
                render_stock_quote(quote)

            with tab2:
                render_search_results(search_response, date_start, date_end)

            with tab3:
                render_analysis_result(analysis_result)


def main() -> None:
    """Streamlit 应用主入口。

    该函数是 Web 应用的入口点，负责处理页面导航和路由。
    """
    # 侧边栏导航
    with st.sidebar:
        st.title("📈 Pocket Stock")

        # 使用 session state 存储当前页面
        if "current_page" not in st.session_state:
            st.session_state.current_page = "home"

        # 页面导航菜单
        page = st.radio(
            "导航",
            ["🏠 主页", "⚙️ 设置"],
            index=0 if st.session_state.current_page == "home" else 1,
            key="page_navigation",
        )

        # 更新当前页面
        if page == "🏠 主页":
            st.session_state.current_page = "home"
        else:
            st.session_state.current_page = "settings"

    # 根据选择的页面渲染内容
    if st.session_state.current_page == "home":
        render_home_page()
    else:
        render_settings_page()


if __name__ == "__main__":
    main()

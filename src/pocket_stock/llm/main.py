"""LLM 股票分析主接口模块。

提供 analyse_stock 主函数，作为模块的公共接口。
"""

from pocket_stock.data_provider.models import StockQuote
from pocket_stock.llm.analyser import LLMStockAnalyser
from pocket_stock.llm.exceptions import (
    ConfigurationError,
    LLMAnalysisError,
)
from pocket_stock.llm.models import StockAnalysisResult
from pocket_stock.search.models import StockSearchResponse


def analyse_stock(stock_quote: StockQuote, stock_news: StockSearchResponse) -> StockAnalysisResult:
    """分析股票并生成投资决策建议。

    这是 LLM 股票分析模块的主接口函数。它接收股票实时行情和新闻资讯，
    使用大语言模型进行分析，并返回结构化的投资决策建议。

    该函数会自动从环境变量加载 LLM 配置，调用 LLM API 进行分析。

    Args:
        stock_quote: 股票实时行情数据，必须包含股票代码、名称、当前价格等核心字段。
        stock_news: 股票相关新闻资讯，包含多个维度的搜索结果。

    Returns:
        结构化的股票分析结果，包含以下信息：
        - stock_name: 股票名称（中文全称）
        - conclusion: 核心结论（该买/该卖/该等）
        - position_suggestion: 持仓分类建议
        - target_prices: 具体狙击点位（买入价、止损价、目标价）
        - checklist: 检查清单

    Raises:
        ConfigurationError: 当缺少必需的配置项或配置无效时抛出。
        LLMApiTimeoutError: 当 LLM API 调用超时时抛出。
        LLMAuthenticationError: 当 API 密钥无效或认证失败时抛出。
        LLMServiceError: 当 LLM 服务返回错误时抛出。
        NetworkConnectionError: 当无法连接到 LLM 服务时抛出。
        LLMResponseParseError: 当无法解析 LLM 响应时抛出。

    Examples:
        >>> from pocket_stock.llm import analyse_stock
        >>> from pocket_stock.data_provider import StockQuote
        >>> from pocket_stock.search import StockSearchResponse
        >>>
        >>> quote = StockQuote(
        ...     stock_code="sh600519",
        ...     name="贵州茅台",
        ...     current_price=1800.00,
        ...     change=10.00,
        ...     change_percent=0.56
        ... )
        >>> news = StockSearchResponse(stock_name="贵州茅台", dimensions={})
        >>> result = analyse_stock(quote, news)
        >>> print(result.conclusion)
        该买
    """
    # 参数验证
    if stock_quote is None:
        raise ValueError("stock_quote 不能为 None")
    if stock_news is None:
        raise ValueError("stock_news 不能为 None")

    # 验证 stock_quote 的核心字段
    if not stock_quote.stock_code:
        raise ValueError("stock_quote.stock_code 不能为空")
    if not stock_quote.name:
        raise ValueError("stock_quote.name 不能为空")
    if stock_quote.current_price is None or stock_quote.current_price < 0:
        raise ValueError("stock_quote.current_price 必须为非负数")

    try:
        # 创建分析器实例并执行分析
        analyser = LLMStockAnalyser.from_env()
        result = analyser.analyse(stock_quote, stock_news)

        return result

    except ConfigurationError:
        # 配置错误直接抛出
        raise

    except LLMAnalysisError:
        # 其他 LLM 相关错误直接抛出
        raise

    except Exception as e:
        # 捕获其他未知异常
        raise LLMAnalysisError(f"股票分析失败: {e}") from e

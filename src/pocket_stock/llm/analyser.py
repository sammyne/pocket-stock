"""LLM 股票分析服务模块。

提供基于大语言模型的股票分析功能，封装 LLM API 调用逻辑。
"""

from typing import Self

from langchain_openai import ChatOpenAI

from pocket_stock.data_provider.models import StockQuote
from pocket_stock.llm.config import LLMConfig
from pocket_stock.llm.exceptions import (
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMServiceError,
    NetworkConnectionError,
)
from pocket_stock.llm.models import (
    StockAnalysisResult,
)
from pocket_stock.search.models import StockSearchResponse


class LLMStockAnalyser:
    """LLM 股票分析服务类。

    使用 LangChain 和 OpenAI 兼容的 API 进行股票分析。

    该类封装了与 LLM 服务交互的所有逻辑，包括提示词生成、
    API 调用和响应解析。

    Attributes:
        llm: LangChain 的 ChatOpenAI 实例。

    Examples:
        >>> from pocket_stock.llm import LLMStockAnalyser
        >>> analyser = LLMStockAnalyser()
        >>> result = analyser.analyse(stock_quote, stock_news)
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        """初始化 LLM 股票分析服务。

        Args:
            config: LLM 配置对象。如果为 None，则从环境变量加载配置。

        Raises:
            ConfigurationError: 当配置无效时抛出。
        """
        self._config = config or LLMConfig()
        self._llm = self._create_llm_instance()

    @classmethod
    def from_env(cls) -> Self:
        """从环境变量创建 LLM 股票分析服务实例。

        Returns:
            LLMStockAnalyser 实例。

        Raises:
            ConfigurationError: 当环境变量配置无效时抛出。
        """
        config = LLMConfig()
        return cls(config)

    def _create_llm_instance(self) -> ChatOpenAI:
        """创建 LangChain ChatOpenAI 实例。

        Returns:
            配置好的 ChatOpenAI 实例。
        """
        return ChatOpenAI(
            model=self._config.openai_model,
            base_url=self._config.openai_api_base_url,
            api_key=self._config.openai_api_key,
            temperature=0.3,  # 降低温度以获得更稳定的输出
            timeout=30,  # 30 秒超时
        )

    def _create_structured_llm(self) -> ChatOpenAI:
        """创建用于结构化输出的 LLM 实例。

        Returns:
            配置好结构化输出的 ChatOpenAI 实例。
        """
        return ChatOpenAI(
            model=self._config.openai_model,
            base_url=self._config.openai_api_base_url,
            api_key=self._config.openai_api_key,
            temperature=0.3,
            timeout=30,
            verbose=True,
        ).with_structured_output(StockAnalysisResult)

    def _build_prompt(self, stock_quote: StockQuote, stock_news: StockSearchResponse) -> str:
        """构建 LLM 提示词。

        将股票行情和新闻资讯格式化为 LLM 可理解的上下文。

        Args:
            stock_quote: 股票实时行情数据。
            stock_news: 股票相关新闻资讯。

        Returns:
            格式化后的提示词字符串。
        """
        # 格式化股票行情信息
        stock_info = f"""
股票代码：{stock_quote.stock_code}
股票名称：{stock_quote.name}
当前价格：{stock_quote.current_price:.2f} 元
涨跌额：{stock_quote.change:+.2f} 元
涨跌幅：{stock_quote.change_percent:+.2f}%
开盘价：{f"{stock_quote.open_price:.2f}" if stock_quote.open_price else "N/A"} 元
收盘价：{f"{stock_quote.close_price:.2f}" if stock_quote.close_price else "N/A"} 元
最高价：{f"{stock_quote.high_price:.2f}" if stock_quote.high_price else "N/A"} 元
最低价：{f"{stock_quote.low_price:.2f}" if stock_quote.low_price else "N/A"} 元
成交量：{stock_quote.volume:,} 手
成交额：{stock_quote.turnover:,.2f} 元
""".strip()

        # 格式化新闻资讯
        news_info = self._format_news(stock_news)

        # 构建完整提示词
        prompt = f"""
你是一位专业的股票投资分析师。请根据以下股票实时行情和相关新闻资讯，提供专业的投资决策建议。

## 股票行情信息
{stock_info}

## 相关新闻资讯
{news_info}

## 分析要求
请基于以上信息，从以下维度进行分析：
1. 股票名称：必须输出正确的中文全称（如"贵州茅台"而非"股票600519"）
2. 核心结论：一句话说清该买/该卖/该等
3. 持仓分类建议：空仓者怎么做 vs 持仓者怎么做
4. 具体狙击点位：买入价、止损价、目标价（精确到分，建议卖出时可为null）
5. 检查清单：每项用 ✅/⚠️/❌ 标记，包含5-10个检查项

注意：
- 确保所有价格精确到分（保留两位小数）
- 当建议为"卖出"时，买入价可为 null
- 检查清单必须包含5-10个检查项
- 股票名称必须是中文全称，不要包含股票代码
""".strip()

        return prompt

    def _format_news(self, stock_news: StockSearchResponse) -> str:
        """格式化新闻资讯信息。

        Args:
            stock_news: 股票相关新闻资讯。

        Returns:
            格式化后的新闻资讯字符串。
        """
        if not stock_news.dimensions:
            return "暂无相关新闻资讯"

        sections = []
        for dimension, response in stock_news.dimensions.items():
            dimension_name = {
                "latest_news": "最新资讯",
                "institution_analysis": "机构分析",
                "risk_analysis": "风险分析",
                "performance_expectation": "业绩预期",
                "industry_analysis": "行业分析",
            }.get(dimension, dimension)

            news_items = []
            for idx, result in enumerate(response.results, 1):
                news_items.append(
                    f"""
{idx}. {result.title}
   来源：{result.source}
   发布时间：{result.published_date.strftime("%Y-%m-%d %H:%M") if result.published_date else "N/A"}
   内容摘要：{result.content}
   URL：{result.url}
""".strip()
                )

            if news_items:
                sections.append(f"\n### {dimension_name}\n" + "\n".join(news_items))

        return "\n".join(sections) if sections else "暂无相关新闻资讯"

    def analyse(self, stock_quote: StockQuote, stock_news: StockSearchResponse) -> StockAnalysisResult:
        """分析股票并生成投资决策建议。

        调用 LLM API 进行股票分析，返回结构化的分析结果。

        Args:
            stock_quote: 股票实时行情数据。
            stock_news: 股票相关新闻资讯。

        Returns:
            结构化的股票分析结果。

        Raises:
            LLMApiTimeoutError: 当 LLM API 调用超时时抛出。
            LLMAuthenticationError: 当 API 密钥无效时抛出。
            LLMServiceError: 当 LLM 服务返回错误时抛出。
            NetworkConnectionError: 当网络连接失败时抛出。
        """
        prompt = self._build_prompt(stock_quote, stock_news)
        structured_llm = self._create_structured_llm()

        try:
            # 调用 LLM API 并直接获取结构化输出
            result = structured_llm.invoke(prompt)
            return result

        except TimeoutError as e:
            raise LLMApiTimeoutError(f"LLM API 调用超时: {e}") from e

        except PermissionError as e:
            raise LLMAuthenticationError(f"LLM API 认证失败，请检查 API 密钥: {e}") from e

        except ConnectionError as e:
            raise NetworkConnectionError(f"无法连接到 LLM 服务: {e}") from e

        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                raise LLMApiTimeoutError(f"LLM API 调用超时: {e}") from e
            if "auth" in error_msg or "permission" in error_msg or "unauthorized" in error_msg:
                raise LLMAuthenticationError(f"LLM API 认证失败: {e}") from e
            if "connection" in error_msg:
                raise NetworkConnectionError(f"网络连接错误: {e}") from e
            raise LLMServiceError(f"LLM 服务返回错误: {e}") from e

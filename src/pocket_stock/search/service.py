"""
搜索服务

提供统一的搜索接口，封装搜索客户端和配置管理。
"""

import asyncio
import logging

from pocket_stock.search.client import AsyncTavilySearchClient
from pocket_stock.search.config import SearchSettings
from pocket_stock.search.exceptions import MissingAPIKeyError, ValidationError
from pocket_stock.search.models import (
    SearchOptions,
    SearchResponse,
    StockSearchDimension,
    StockSearchResponse,
)

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务

    提供统一的搜索接口，支持异步搜索。
    """

    def __init__(
        self,
        api_key: str | None = None,
    ) -> None:
        """初始化搜索服务

        Args:
            api_key: 可选的 API key，如果提供则覆盖环境变量
        """
        # 初始化配置
        try:
            if api_key:
                self._settings = SearchSettings(api_key=api_key)
            else:
                self._settings = SearchSettings()
        except ValueError as e:
            raise MissingAPIKeyError(str(e)) from e

        # 初始化客户端
        self._client: AsyncTavilySearchClient = AsyncTavilySearchClient(self._settings)

        logger.info("搜索服务初始化完成")

    async def search(
        self,
        query: str,
        config: SearchOptions | None = None,
    ) -> SearchResponse:
        """执行搜索

        Args:
            query: 搜索查询字符串
            config: 搜索配置，如果为 None 则使用默认配置

        Returns:
            搜索响应对象

        Raises:
            ValidationError: 当查询参数无效时抛出
            NetworkError: 当网络请求失败时抛出
            ServiceError: 当服务返回错误时抛出
            AuthenticationError: 当认证失败时抛出
            RateLimitError: 当达到速率限制时抛出
        """
        logger.info(f"执行搜索: query='{query}'")

        response = await self._client.search(query, config)

        logger.info(f"搜索成功: result_count={response.result_count}, response_time={response.response_time:.3f}s")

        return response

    async def search_multiple(
        self,
        queries: list[str],
        config: SearchOptions | None = None,
    ) -> list[SearchResponse]:
        """并发执行多个搜索查询

        Args:
            queries: 查询字符串列表
            config: 搜索配置，如果为 None 则使用默认配置

        Returns:
            搜索响应列表

        Raises:
            ValidationError: 当查询参数无效时抛出
            NetworkError: 当网络请求失败时抛出
            ServiceError: 当服务返回错误时抛出
        """
        if not queries:
            raise ValidationError("查询列表不能为空")

        logger.info(f"执行并发搜索: query_count={len(queries)}")

        responses = await self._client.search_multiple(queries, config)

        total_results = sum(r.result_count for r in responses)
        total_time = sum(r.response_time for r in responses)

        logger.info(
            f"并发搜索成功: query_count={len(queries)}, total_results={total_results}, "
            f"total_time={total_time:.3f}s"
        )

        return responses

    async def search_stock(
        self,
        stock_name: str,
        config: SearchOptions | None = None,
    ) -> StockSearchResponse:
        """从多个维度搜索指定股票的相关新闻

        Args:
            stock_name: 股票名称
            config: 搜索配置，如果为 None 则使用默认配置

        Returns:
            股票搜索响应对象，包含各维度的搜索结果

        Raises:
            ValidationError: 当股票名称无效时抛出
            NetworkError: 当网络请求失败时抛出
            ServiceError: 当服务返回错误时抛出
        """
        if not stock_name or not stock_name.strip():
            raise ValidationError("股票名称不能为空")

        stock_name = stock_name.strip()

        logger.info(f"执行股票搜索: stock_name='{stock_name}'")

        # 定义各维度的搜索查询
        dimension_queries = {
            StockSearchDimension.LATEST_NEWS: f"{stock_name} 最新消息 新闻",
            StockSearchDimension.INSTITUTION_ANALYSIS: f"{stock_name} 机构分析 研报 券商评级",
            StockSearchDimension.RISK_ANALYSIS: f"{stock_name} 风险排查 风险预警 负面新闻",
            StockSearchDimension.PERFORMANCE_EXPECTATION: f"{stock_name} 业绩预期 业绩预告 业绩预测",
            StockSearchDimension.INDUSTRY_ANALYSIS: f"{stock_name} 行业分析 行业动态 行业趋势",
        }

        # 并发执行各维度的搜索
        tasks = [self._client.search(query, config) for query in dimension_queries.values()]
        responses = await asyncio.gather(*tasks)

        # 构建维度到响应的映射
        dimension_results: dict[StockSearchDimension, SearchResponse] = {}
        for i, dimension in enumerate(dimension_queries.keys()):
            dimension_results[dimension] = responses[i]

        # 构建股票搜索响应
        total_time = sum(response.response_time for response in responses)
        stock_response = StockSearchResponse(
            stock_name=stock_name,
            dimensions=dimension_results,
            total_time=total_time,
        )

        logger.info(
            f"股票搜索成功: stock_name='{stock_name}', dimension_count={stock_response.dimension_count}, "
            f"total_results={stock_response.total_results}, total_time={total_time:.3f}s"
        )

        return stock_response

    @property
    def api_key(self) -> str:
        """获取 API key（已隐藏敏感信息）

        Returns:
            隐藏的 API key
        """
        return "***"

    def validate_config(self) -> bool:
        """验证配置是否有效

        Returns:
            如果配置有效返回 True

        Raises:
            ConfigurationError: 当配置无效时抛出
        """
        return self._settings.validate()

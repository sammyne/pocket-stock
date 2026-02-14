"""
Tavily 搜索服务客户端

封装 Tavily API 调用，提供同步和异步搜索功能。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import aiohttp
import httpx
from tavily import AsyncTavilyClient, TavilyClient

from pocket_stock.search.config import SearchSettings
from pocket_stock.search.exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServiceError,
    ValidationError,
)
from pocket_stock.search.models import SearchOptions, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class TavilySearchClient:
    """Tavily 搜索客户端

    提供同步搜索功能，封装 Tavily API 调用。
    """

    def __init__(self, settings: SearchSettings) -> None:
        """初始化 Tavily 搜索客户端

        Args:
            settings: 搜索配置
        """
        self._settings = settings
        self._client = TavilyClient(api_key=settings.api_key)

    def search(
        self,
        query: str,
        config: SearchOptions | None = None,
    ) -> SearchResponse:
        """执行同步搜索

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
        # 验证查询参数
        if not query or not query.strip():
            raise ValidationError("查询字符串不能为空")

        # 使用默认配置
        if config is None:
            config = SearchOptions()

        # 记录开始时间
        start_time = datetime.now()

        try:
            # 构建搜索参数
            search_params = self._build_search_params(query, config)

            # 记录请求（不包含敏感信息）
            logger.info(f"执行搜索查询: query='{query}'")

            # 调用 Tavily API
            response = self._client.search(**search_params)

            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()

            # 记录响应
            logger.info(f"搜索完成: 结果数量={len(response.get('results', []))}, 耗时={response_time:.3f}秒")

            # 转换响应
            return self._convert_response(query, response, response_time)

        except AuthenticationError as e:
            logger.error(f"认证失败: {e.message}")
            raise
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP 错误: status_code={status_code}, message={e.response.text}")

            if status_code == 401:
                raise AuthenticationError() from e
            elif status_code == 429:
                raise RateLimitError() from e
            else:
                raise ServiceError(f"HTTP 错误: {status_code}", status_code=status_code) from e
        except httpx.RequestError as e:
            logger.error(f"网络请求失败: {str(e)}")
            raise NetworkError(f"网络请求失败: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {str(e)}")
            raise ServiceError(f"响应解析失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise ServiceError(f"搜索失败: {str(e)}") from e

    def _build_search_params(self, query: str, config: SearchOptions) -> dict[str, Any]:
        """构建搜索参数

        Args:
            query: 查询字符串
            config: 搜索配置

        Returns:
            搜索参数字典
        """
        params: dict[str, Any] = {
            "query": query,
            "max_results": config.max_results,
            "search_depth": config.search_depth.value,
        }

        # 可选参数
        if config.time_range:
            params["time_range"] = config.time_range.value

        if config.include_domains:
            params["include_domains"] = config.include_domains

        if config.exclude_domains:
            params["exclude_domains"] = config.exclude_domains

        if config.include_answer:
            params["include_answer"] = True

        if config.include_raw_content:
            params["include_raw_content"] = True

        if config.include_images:
            params["include_images"] = True

        return params

    def _convert_response(self, query: str, raw_response: dict[str, Any], response_time: float) -> SearchResponse:
        """转换 Tavily 响应为标准响应

        Args:
            query: 查询字符串
            raw_response: Tavily 原始响应
            response_time: 响应时间

        Returns:
            标准化的搜索响应
        """
        results: list[SearchResult] = []

        # 转换搜索结果
        for item in raw_response.get("results", []):
            result = SearchResult(
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                source=item.get("url", "").split("/")[2] if item.get("url") else "",
                published_date=self._parse_date(item.get("published_date")),
                score=item.get("score", 0.0),
            )
            results.append(result)

        return SearchResponse(
            query=query,
            results=results,
            answer=raw_response.get("answer"),
            images=raw_response.get("images"),
            response_time=response_time,
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            解析后的 datetime 对象，如果解析失败则返回 None
        """
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


class AsyncTavilySearchClient:
    """异步 Tavily 搜索客户端

    提供异步搜索功能，支持并发请求。
    """

    def __init__(self, settings: SearchSettings) -> None:
        """初始化异步 Tavily 搜索客户端

        Args:
            settings: 搜索配置
        """
        self._settings = settings
        self._client = AsyncTavilyClient(api_key=settings.api_key)

    async def search(
        self,
        query: str,
        config: SearchOptions | None = None,
    ) -> SearchResponse:
        """执行异步搜索

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
        # 验证查询参数
        if not query or not query.strip():
            raise ValidationError("查询字符串不能为空")

        # 使用默认配置
        if config is None:
            config = SearchOptions()

        # 记录开始时间
        start_time = datetime.now()

        try:
            # 构建搜索参数
            search_params = self._build_search_params(query, config)

            # 记录请求（不包含敏感信息）
            logger.info(f"执行异步搜索查询: query='{query}'")

            # 调用 Tavily API
            response = await self._client.search(**search_params)

            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()

            # 记录响应
            logger.info(f"异步搜索完成: 结果数量={len(response.get('results', []))}, 耗时={response_time:.3f}秒")

            # 转换响应
            return self._convert_response(query, response, response_time)

        except AuthenticationError as e:
            logger.error(f"认证失败: {e.message}")
            raise
        except aiohttp.ClientResponseError as e:
            status_code = e.status
            logger.error(f"HTTP 错误: status_code={status_code}, message={e.message}")

            if status_code == 401:
                raise AuthenticationError() from e
            elif status_code == 429:
                raise RateLimitError() from e
            else:
                raise ServiceError(f"HTTP 错误: {status_code}", status_code=status_code) from e
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {str(e)}")
            raise NetworkError(f"网络请求失败: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {str(e)}")
            raise ServiceError(f"响应解析失败: {str(e)}") from e
        except asyncio.CancelledError:
            logger.warning("异步搜索被取消")
            raise
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise ServiceError(f"搜索失败: {str(e)}") from e

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

        logger.info(f"并发执行 {len(queries)} 个搜索查询")

        # 并发执行搜索
        tasks = [self.search(query, config) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        logger.info(f"并发搜索完成: 成功={len(results)}")

        return results

    def _build_search_params(self, query: str, config: SearchOptions) -> dict[str, Any]:
        """构建搜索参数

        Args:
            query: 查询字符串
            config: 搜索配置

        Returns:
            搜索参数字典
        """
        params: dict[str, Any] = {
            "query": query,
            "max_results": config.max_results,
            "search_depth": config.search_depth.value,
        }

        # 可选参数
        if config.time_range:
            params["time_range"] = config.time_range.value

        if config.include_domains:
            params["include_domains"] = config.include_domains

        if config.exclude_domains:
            params["exclude_domains"] = config.exclude_domains

        if config.include_answer:
            params["include_answer"] = True

        if config.include_raw_content:
            params["include_raw_content"] = True

        if config.include_images:
            params["include_images"] = True

        return params

    def _convert_response(self, query: str, raw_response: dict[str, Any], response_time: float) -> SearchResponse:
        """转换 Tavily 响应为标准响应

        Args:
            query: 查询字符串
            raw_response: Tavily 原始响应
            response_time: 响应时间

        Returns:
            标准化的搜索响应
        """
        results: list[SearchResult] = []

        # 转换搜索结果
        for item in raw_response.get("results", []):
            result = SearchResult(
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                source=item.get("url", "").split("/")[2] if item.get("url") else "",
                published_date=self._parse_date(item.get("published_date")),
                score=item.get("score", 0.0),
            )
            results.append(result)

        return SearchResponse(
            query=query,
            results=results,
            answer=raw_response.get("answer"),
            images=raw_response.get("images"),
            response_time=response_time,
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            解析后的 datetime 对象，如果解析失败则返回 None
        """
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

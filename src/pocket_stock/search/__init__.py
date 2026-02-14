"""
搜索模块

提供统一的搜索接口，支持 Tavily 搜索服务集成。

该模块封装了 Tavily API，提供同步和异步搜索功能，
支持可配置的搜索选项，如搜索深度、结果数量、时间范围等。
"""

from pocket_stock.search.config import SearchSettings
from pocket_stock.search.exceptions import (
    AuthenticationError,
    ConfigurationError,
    MissingAPIKeyError,
    NetworkError,
    RateLimitError,
    SearchError,
    ServiceError,
    ValidationError,
)
from pocket_stock.search.models import SearchDepth, SearchOptions, SearchResponse, SearchResult, SearchTimeRange
from pocket_stock.search.service import SearchService

__all__ = [
    "SearchService",
    "SearchResult",
    "SearchOptions",
    "SearchDepth",
    "SearchTimeRange",
    "SearchResponse",
    "SearchSettings",
    "SearchError",
    "ConfigurationError",
    "MissingAPIKeyError",
    "NetworkError",
    "ServiceError",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
]

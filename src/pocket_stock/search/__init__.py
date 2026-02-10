"""
搜索模块

提供统一的搜索接口，支持 Tavily 搜索服务集成。

该模块封装了 Tavily API，提供同步和异步搜索功能，
支持可配置的搜索选项，如搜索深度、结果数量、时间范围等。
"""

from pocket_stock.search.service import SearchService
from pocket_stock.search.models import SearchResult, SearchConfig, SearchDepth, SearchTimeRange, SearchResponse
from pocket_stock.search.config import SearchSettings
from pocket_stock.search.exceptions import (
    SearchError,
    ConfigurationError,
    MissingAPIKeyError,
    NetworkError,
    ServiceError,
    ValidationError,
    RateLimitError,
    AuthenticationError,
)

__all__ = [
    "SearchService",
    "SearchResult",
    "SearchConfig",
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

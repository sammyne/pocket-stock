"""搜索服务单元测试。"""

from datetime import datetime

import pytest

from pocket_stock.search.config import SearchSettings
from pocket_stock.search.exceptions import (
    ValidationError,
)
from pocket_stock.search.models import SearchOptions
from pocket_stock.search.service import SearchService


class TestSearchService:
    """SearchService 测试类。"""

    def test_init_with_api_key(self) -> None:
        """测试使用 API key 初始化服务。"""
        service = SearchService(api_key="test_api_key_12345678")
        assert service.api_key == "***"

    def test_validate_config(self) -> None:
        """测试配置验证。"""
        service = SearchService(api_key="test_api_key_12345678")
        assert service.validate_config() is True


class TestSearchClientHelperMethods:
    """搜索客户端辅助方法测试。"""

    def _get_settings(self) -> SearchSettings:
        """获取测试用的 SearchSettings"""
        return SearchSettings.model_construct(api_key="test_api_key_12345678")

    def test_parse_date_valid_iso(self) -> None:
        """测试解析有效的 ISO 日期。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        date_str = "2024-01-15T10:30:00Z"
        result = client._parse_date(date_str)
        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_date_none(self) -> None:
        """测试解析 None 日期。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        result = client._parse_date(None)
        assert result is None

    def test_parse_date_empty_string(self) -> None:
        """测试解析空字符串日期。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        result = client._parse_date("")
        assert result is None

    def test_parse_date_invalid_format(self) -> None:
        """测试解析无效格式的日期。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        result = client._parse_date("invalid-date")
        assert result is None

    def test_build_search_params_default(self) -> None:
        """测试使用默认配置构建搜索参数。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        config = SearchOptions()
        params = client._build_search_params("test query", config)

        assert params["query"] == "test query"
        assert params["max_results"] == config.max_results
        assert "search_depth" in params
        assert "time_range" not in params
        assert "include_domains" not in params

    def test_build_search_params_with_optional_fields(self) -> None:
        """测试使用可选字段构建搜索参数。"""
        from pocket_stock.search.client import TavilySearchClient
        from pocket_stock.search.models import SearchDepth

        client = TavilySearchClient(self._get_settings())
        config = SearchOptions(
            search_depth=SearchDepth.ADVANCED,
            include_domains=["example.com"],
            exclude_domains=["spam.com"],
            include_answer=True,
            include_raw_content=True,
            include_images=True,
        )
        params = client._build_search_params("test query", config)

        assert params["query"] == "test query"
        assert params["search_depth"] == "advanced"
        assert params["include_domains"] == ["example.com"]
        assert params["exclude_domains"] == ["spam.com"]
        assert params["include_answer"] is True
        assert params["include_raw_content"] is True
        assert params["include_images"] is True

    def test_convert_response_basic(self) -> None:
        """测试转换基本响应。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        raw_response = {
            "results": [
                {
                    "title": "Test Title",
                    "content": "Test content",
                    "url": "https://example.com/article",
                    "score": 0.95,
                }
            ]
        }

        response = client._convert_response("test query", raw_response, 1.5)

        assert response.query == "test query"
        assert response.response_time == 1.5
        assert len(response.results) == 1
        assert response.results[0].title == "Test Title"
        assert response.results[0].source == "example.com"

    def test_convert_response_with_optional_fields(self) -> None:
        """测试转换包含可选字段的响应。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        raw_response = {
            "results": [],
            "answer": "Test answer",
            "images": ["https://example.com/image.jpg"],
        }

        response = client._convert_response("test query", raw_response, 0.5)

        assert response.answer == "Test answer"
        assert response.images == ["https://example.com/image.jpg"]

    def test_convert_response_empty_results(self) -> None:
        """测试转换空结果响应。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())
        raw_response = {"results": []}

        response = client._convert_response("test query", raw_response, 0.1)

        assert len(response.results) == 0
        assert response.result_count == 0

    def test_search_validation_empty_query(self) -> None:
        """测试空查询字符串验证。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())

        with pytest.raises(ValidationError, match="查询字符串不能为空"):
            client.search("")

    def test_search_validation_whitespace_query(self) -> None:
        """测试空白查询字符串验证。"""
        from pocket_stock.search.client import TavilySearchClient

        client = TavilySearchClient(self._get_settings())

        with pytest.raises(ValidationError, match="查询字符串不能为空"):
            client.search("   ")

    def test_async_client_helper_methods(self) -> None:
        """测试异步客户端的辅助方法。"""
        from pocket_stock.search.client import AsyncTavilySearchClient

        client = AsyncTavilySearchClient(self._get_settings())

        # 测试 _parse_date
        result = client._parse_date("2024-01-15T10:30:00Z")
        assert result is not None
        assert isinstance(result, datetime)

        # 测试 _build_search_params
        config = SearchOptions()
        params = client._build_search_params("test", config)
        assert params["query"] == "test"

        # 测试 _convert_response
        raw_response = {"results": []}
        response = client._convert_response("test", raw_response, 0.5)
        assert response.query == "test"

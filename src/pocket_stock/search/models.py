"""
搜索结果数据模型

定义搜索功能相关的数据模型，使用 Pydantic 进行数据验证。
"""

from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SearchDepth(StrEnum):
    """搜索深度枚举"""

    BASIC = "basic"
    ADVANCED = "advanced"


class SearchTimeRange(StrEnum):
    """搜索时间范围枚举"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SearchResult(BaseModel):
    """搜索结果模型

    表示单个搜索结果，包含标题、内容、来源等基本信息。
    """

    title: str = Field(description="搜索结果标题")
    content: str = Field(description="搜索结果内容摘要")
    url: str = Field(description="来源 URL")
    source: str = Field(description="来源网站名称")
    published_date: Optional[datetime] = Field(default=None, description="发布时间")
    score: float = Field(default=0.0, description="相关性评分")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证 URL 格式"""
        if not v:
            raise ValueError("URL 不能为空")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        return v

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """验证评分范围"""
        if v < 0 or v > 1:
            raise ValueError("评分必须在 0 到 1 之间")
        return v

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class SearchConfig(BaseModel):
    """搜索配置模型

    定义搜索的配置选项，包括搜索深度、结果数量、时间范围等。
    """

    max_results: int = Field(default=3, ge=1, le=20, description="最大结果数量，1-20")
    search_depth: SearchDepth = Field(default=SearchDepth.BASIC, description="搜索深度")
    time_range: Optional[SearchTimeRange] = Field(default=None, description="搜索时间范围")
    include_domains: Optional[list[str]] = Field(default=None, description="包含的域名列表")
    exclude_domains: Optional[list[str]] = Field(default=None, description="排除的域名列表")
    include_answer: bool = Field(default=False, description="是否包含 AI 生成的答案")
    include_raw_content: bool = Field(default=False, description="是否包含原始内容")
    include_images: bool = Field(default=False, description="是否包含图片")

    @model_validator(mode="after")
    def validate_domains(self) -> "SearchConfig":
        """验证域名列表"""
        if self.include_domains:
            for domain in self.include_domains:
                if not domain.strip():
                    raise ValueError("包含的域名不能为空字符串")
        if self.exclude_domains:
            for domain in self.exclude_domains:
                if not domain.strip():
                    raise ValueError("排除的域名不能为空字符串")
        return self


class SearchResponse(BaseModel):
    """搜索响应模型

    表示搜索 API 的完整响应，包含结果列表和元数据。
    """

    query: str = Field(description="搜索查询字符串")
    results: list[SearchResult] = Field(default_factory=list, description="搜索结果列表")
    answer: Optional[str] = Field(default=None, description="AI 生成的答案")
    images: Optional[list[str]] = Field(default=None, description="图片 URL 列表")
    response_time: float = Field(default=0.0, description="响应时间（秒）")

    @property
    def result_count(self) -> int:
        """获取结果数量"""
        return len(self.results)


class StockSearchDimension(StrEnum):
    """股票搜索维度枚举"""

    LATEST_NEWS = "latest_news"
    INSTITUTION_ANALYSIS = "institution_analysis"
    RISK_ANALYSIS = "risk_analysis"
    PERFORMANCE_EXPECTATION = "performance_expectation"
    INDUSTRY_ANALYSIS = "industry_analysis"


class StockSearchResponse(BaseModel):
    """股票搜索响应模型

    表示从多个维度搜索股票信息的响应结果。
    """

    stock_name: str = Field(description="股票名称")
    dimensions: dict[StockSearchDimension, SearchResponse] = Field(
        default_factory=dict, description="各维度的搜索结果"
    )
    total_time: float = Field(default=0.0, description="总响应时间（秒）")

    @property
    def dimension_count(self) -> int:
        """获取搜索维度数量"""
        return len(self.dimensions)

    @property
    def total_results(self) -> int:
        """获取所有维度的结果总数"""
        return sum(response.result_count for response in self.dimensions.values())

"""
搜索结果数据模型

定义搜索功能相关的数据模型，使用 Pydantic 进行数据验证。
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class SearchDepth(StrEnum):
    """搜索深度枚举

    控制延迟与相关性的权衡以及如何生成结果内容。
    """

    BASIC = "basic"
    ADVANCED = "advanced"
    FAST = "fast"
    ULTRA_FAST = "ultra-fast"


class SearchTopic(StrEnum):
    """搜索主题枚举"""

    GENERAL = "general"
    NEWS = "news"
    FINANCE = "finance"


class IncludeAnswerLevel(StrEnum):
    """包含答案级别枚举"""

    BASIC = "basic"
    ADVANCED = "advanced"


class IncludeRawContentFormat(StrEnum):
    """包含原始内容格式枚举"""

    MARKDOWN = "markdown"
    TEXT = "text"


class SearchTimeRange(StrEnum):
    """搜索时间范围枚举"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    # 简写形式
    D = "d"
    W = "w"
    M = "m"
    Y = "y"


class SearchResult(BaseModel):
    """搜索结果模型

    表示单个搜索结果，包含标题、内容、来源等基本信息。
    """

    title: str = Field(description="搜索结果标题")
    content: str = Field(description="搜索结果内容摘要")
    url: str = Field(description="来源 URL")
    source: str = Field(description="来源网站名称")
    published_date: datetime | None = Field(default=None, description="发布时间")
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


class SearchOptions(BaseModel):
    """搜索选项模型

    定义搜索的配置选项，包括搜索深度、结果数量、时间范围等。
    完整支持 Tavily Search API 的所有请求参数。
    """

    max_results: int = Field(default=5, ge=0, le=20, description="最大结果数量，0-20")
    search_depth: SearchDepth = Field(default=SearchDepth.BASIC, description="搜索深度")
    chunks_per_source: int = Field(
        default=3, ge=1, le=3, description="每个源返回的最大 chunk 数量，仅在 search_depth 为 advanced 时可用"
    )
    topic: SearchTopic = Field(default=SearchTopic.GENERAL, description="搜索主题类别")
    time_range: SearchTimeRange | None = Field(default=None, description="搜索时间范围")
    start_date: str | None = Field(
        default=None,
        description="起始日期，格式为 YYYY-MM-DD，返回该日期之后的结果",
    )
    end_date: str | None = Field(
        default=None,
        description="结束日期，格式为 YYYY-MM-DD，返回该日期之前的结果",
    )
    include_answer: bool | IncludeAnswerLevel = Field(
        default=False, description="是否包含 AI 生成的答案，true/basic 返回快速答案，advanced 返回详细答案"
    )
    include_raw_content: bool | IncludeRawContentFormat = Field(
        default=False,
        description="是否包含原始内容，markdown/true 返回 markdown 格式，text 返回纯文本",
    )
    include_images: bool = Field(default=False, description="是否包含图片搜索结果")
    include_image_descriptions: bool = Field(
        default=False, description="当 include_images 为 true 时，是否为每张图片添加描述文本"
    )
    include_favicon: bool = Field(default=False, description="是否包含每个结果的 favicon URL")
    include_domains: list[str] | None = Field(default=None, max_length=300, description="包含的域名列表，最多 300 个")
    exclude_domains: list[str] | None = Field(default=None, max_length=150, description="排除的域名列表，最多 150 个")
    country: str | None = Field(default="china", description="优先显示来自特定国家的内容，仅在 topic 为 general 时可用")
    auto_parameters: bool = Field(
        default=False,
        description="是否自动配置搜索参数，Tavily 会根据查询内容和意图自动配置参数",
    )
    include_usage: bool = Field(default=False, description="是否在响应中包含 credit 使用信息")

    @model_validator(mode="after")
    def validate_domains(self) -> "SearchOptions":
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

    @model_validator(mode="after")
    def validate_date_format(self) -> "SearchOptions":
        """验证日期格式"""
        date_format = "%Y-%m-%d"
        if self.start_date:
            try:
                datetime.strptime(self.start_date, date_format)
            except ValueError as err:
                raise ValueError(f"start_date 格式错误，应为 YYYY-MM-DD，当前为: {self.start_date}") from err
        if self.end_date:
            try:
                datetime.strptime(self.end_date, date_format)
            except ValueError as err:
                raise ValueError(f"end_date 格式错误，应为 YYYY-MM-DD，当前为: {self.end_date}") from err
        return self

    @model_validator(mode="after")
    def validate_country_with_topic(self) -> "SearchOptions":
        """验证 country 参数仅在 topic 为 general 时可用"""
        if self.country and self.topic != SearchTopic.GENERAL:
            raise ValueError("country 参数仅在 topic 为 general 时可用")
        return self


class SearchResponse(BaseModel):
    """搜索响应模型

    表示搜索 API 的完整响应，包含结果列表和元数据。
    """

    query: str = Field(description="搜索查询字符串")
    results: list[SearchResult] = Field(default_factory=list, description="搜索结果列表")
    answer: str | None = Field(default=None, description="AI 生成的答案")
    images: list[str] | None = Field(default=None, description="图片 URL 列表")
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
    dimensions: dict[StockSearchDimension, SearchResponse] = Field(default_factory=dict, description="各维度的搜索结果")
    total_time: float = Field(default=0.0, description="总响应时间（秒）")

    @property
    def dimension_count(self) -> int:
        """获取搜索维度数量"""
        return len(self.dimensions)

    @property
    def total_results(self) -> int:
        """获取所有维度的结果总数"""
        return sum(response.result_count for response in self.dimensions.values())

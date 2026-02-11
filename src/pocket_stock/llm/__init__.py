"""LLM 股票分析模块。

该模块提供基于大语言模型的股票分析功能，包括：
- analyse_stock 主函数：接收股票实时行情和新闻资讯，生成结构化的投资决策建议
- LLMStockAnalyser 服务类：封装 LLM API 调用逻辑
- 数据模型：定义分析结果的结构化格式
"""

from .analyser import LLMStockAnalyser
from .config import LLMConfig
from .exceptions import (
    ConfigurationError,
    LLMApiTimeoutError,
    LLMAuthenticationError,
    LLMResponseParseError,
    LLMServiceError,
    NetworkConnectionError,
)
from .main import analyse_stock
from .models import (
    ChecklistItem,
    PositionSuggestion,
    StockAnalysisResult,
    TargetPrices,
)

__all__ = [
    "analyse_stock",
    "LLMStockAnalyser",
    "LLMConfig",
    "ConfigurationError",
    "LLMApiTimeoutError",
    "LLMAuthenticationError",
    "LLMServiceError",
    "NetworkConnectionError",
    "LLMResponseParseError",
    "StockAnalysisResult",
    "PositionSuggestion",
    "TargetPrices",
    "ChecklistItem",
]

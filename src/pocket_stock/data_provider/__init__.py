"""金融数据获取模块。

该模块提供从腾讯财经获取股票实时行情的功能，支持异步操作。
"""

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    DataParseException,
    DataProviderError,
    DataValidationException,
    InvalidStockCodeException,
    NetworkErrorException,
    ProviderServiceErrorException,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.parser import TencentFinanceParser
from pocket_stock.data_provider.provider import StockDataProvider

__all__ = [
    # 配置
    "ProviderConfig",
    # 数据模型
    "StockQuote",
    # 数据提供者
    "StockDataProvider",
    # 解析器
    "TencentFinanceParser",
    # 异常
    "DataProviderError",
    "InvalidStockCodeException",
    "NetworkErrorException",
    "ProviderServiceErrorException",
    "DataParseException",
    "DataValidationException",
]

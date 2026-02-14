"""股票数据提供者基类及具体实现。"""

import abc
import asyncio
from typing import Any

import aiohttp

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    InvalidStockCodeError,
    NetworkError,
    ProviderServiceError,
)
from pocket_stock.data_provider.logger import log_error, log_request, log_response
from pocket_stock.data_provider.models import StockQuote


class BaseStockDataProvider(abc.ABC):
    """股票数据提供者基类。

    定义获取股票数据的通用接口，包括股票代码验证、数据获取、
    日志记录和异常处理等通用功能。

    子类需要实现抽象方法 `_get` 来具体获取原始数据。

    Attributes:
        config: 配置对象
        session: aiohttp 异步 HTTP 客户端会话
        _owned_session: 是否拥有会话的所有权（用于在退出时关闭会话）

    Examples:
        >>> class MyProvider(BaseStockDataProvider):
        ...     async def _get(self, stock_code: str) -> str:
        ...         # 实现具体的数据获取逻辑
        ...         return "raw_data"
    """

    def __init__(
        self,
        config: ProviderConfig,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """初始化数据提供者。

        Args:
            config: 配置对象
            session: 自定义异步 HTTP 客户端会话（可选）。
                如果未提供，将创建一个新的会话。

        Examples:
            >>> config = ProviderConfig(timeout=10.0)
            >>> provider = MyProvider(config)
        """
        self.config = config
        self.session = session
        self._owned_session = session is None

    async def __aenter__(self) -> "BaseStockDataProvider":
        """异步上下文管理器入口。

        创建 HTTP 会话（如果尚未创建）。

        Returns:
            自身实例
        """
        if self._owned_session and self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """异步上下文管理器出口。

        关闭拥有的 HTTP 会话。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪
        """
        if self._owned_session and self.session:
            await self.session.close()

    @abc.abstractmethod
    async def _get(self, stock_code: str) -> StockQuote:
        """获取股票行情数据。

        子类必须实现此方法，从数据提供者获取并解析数据。

        Args:
            stock_code: 股票代码

        Returns:
            股票行情数据对象

        Raises:
            NetworkError: 网络错误
            ProviderServiceError: 服务错误
            DataParseError: 数据解析错误
        """
        pass

    async def get(self, stock_code: str) -> StockQuote:
        """获取股票行情数据。

        检查股票代码合法性，调用子类实现的 `_get` 方法获取并返回行情数据。

        Args:
            stock_code: 股票代码（如 "sh600000"、"sz000001"）

        Returns:
            股票行情数据对象

        Raises:
            InvalidStockCodeError: 当股票代码无效时
            NetworkError: 当网络连接失败或超时时
            ProviderServiceError: 当数据提供者返回错误状态码时

        Examples:
            >>> provider = MyProvider(ProviderConfig())
            >>> async with provider:
            ...     quote = await provider.get("sh600000")
            ...     print(f"股票名称: {quote.name}, 当前价格: {quote.current_price}")
        """
        # 验证股票代码格式
        self._validate_stock_code(stock_code)

        # 记录请求日志
        await log_request(stock_code, timeout=self.config.timeout)

        try:
            # 获取并解析数据（由子类实现）
            start_time = asyncio.get_event_loop().time()
            quote = await self._get(stock_code)
            elapsed_time = asyncio.get_event_loop().time() - start_time

            # 记录响应日志
            await log_response(stock_code, elapsed_time, status="success")

            return quote

        except InvalidStockCodeError:
            raise
        except NetworkError:
            raise
        except ProviderServiceError:
            raise
        except Exception as e:
            # 记录错误日志
            await log_error(e, stock_code=stock_code)
            raise

    async def close(self) -> None:
        """关闭资源。

        如果使用了内部创建的会话，则关闭它。
        """
        if self._owned_session and self.session:
            await self.session.close()

    @staticmethod
    def _validate_stock_code(stock_code: str) -> None:
        """验证股票代码格式。

        Args:
            stock_code: 待验证的股票代码

        Raises:
            InvalidStockCodeError: 当股票代码格式不正确时抛出
        """
        if not stock_code or len(stock_code) != 8:
            raise InvalidStockCodeError(f'无效的股票代码格式: "{stock_code}"，应为8位字符（如 sh600000 或 sz000001）')

        prefix = stock_code[:2].lower()
        suffix = stock_code[2:]

        if prefix not in ("sh", "sz"):
            raise InvalidStockCodeError(f'无效的股票代码格式: "{stock_code}"，应以 "sh" 或 "sz" 开头')

        if not suffix.isdigit():
            raise InvalidStockCodeError(f'无效的股票代码格式: "{stock_code}"，后6位应为数字')

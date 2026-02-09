"""股票数据提供者。"""

import asyncio
import logging
from typing import Any

import aiohttp

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    InvalidStockCodeException,
    NetworkErrorException,
    ProviderServiceErrorException,
)
from pocket_stock.data_provider.logger import log_error, log_request, log_response, setup_logger
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.parser import TencentFinanceParser


class StockDataProvider:
    """股票数据提供者。

    该类提供从腾讯财经获取股票实时行情的异步接口。

    Attributes:
        config: 配置对象
        session: aiohttp 异步 HTTP 客户端会话
        parser: 数据解析器

    Examples:
        >>> config = ProviderConfig(timeout=10.0)
        >>> provider = StockDataProvider(config)
        >>> quote = await provider.get_stock_quote("sh600000")
        >>> print(f"股票名称: {quote.name}, 当前价格: {quote.current_price}")
    """

    # 腾讯财经 API URL
    _API_URL = "https://qt.gtimg.cn/q={stock_code}"

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
            >>> provider = StockDataProvider(config)
        """
        self.config = config
        self.session = session
        self.parser = TencentFinanceParser()
        self._owned_session = session is None

    async def __aenter__(self) -> "StockDataProvider":
        """异步上下文管理器入口。"""
        if self._owned_session and self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """异步上下文管理器出口。"""
        if self._owned_session and self.session:
            await self.session.close()

    async def get_stock_quote(self, stock_code: str) -> StockQuote:
        """异步获取指定股票的实时行情。

        Args:
            stock_code: 股票代码（如 "sh600000"、"sz000001"）

        Returns:
            股票行情数据对象

        Raises:
            InvalidStockCodeException: 当股票代码无效时
            NetworkErrorException: 当网络连接失败或超时时
            ProviderServiceErrorException: 当数据提供者返回错误状态码时

        Examples:
            >>> provider = StockDataProvider(ProviderConfig())
            >>> async with provider:
            ...     quote = await provider.get_stock_quote("sh600000")
            ...     print(f"股票名称: {quote.name}, 当前价格: {quote.current_price}")
        """
        # 验证股票代码格式
        self._validate_stock_code(stock_code)

        # 记录请求日志
        await log_request(stock_code, timeout=self.config.timeout)

        try:
            # 构建 API URL
            url = self._API_URL.format(stock_code=stock_code)

            # 发起异步 HTTP 请求
            start_time = asyncio.get_event_loop().time()
            response_text = await self._fetch_data(url)
            elapsed_time = asyncio.get_event_loop().time() - start_time

            # 解析数据
            quote = await self.parser.parse(response_text, stock_code)

            # 记录响应日志
            await log_response(stock_code, elapsed_time, status="success")

            return quote

        except InvalidStockCodeException:
            raise
        except NetworkErrorException:
            raise
        except ProviderServiceErrorException:
            raise
        except Exception as e:
            # 记录错误日志
            await log_error(e, stock_code=stock_code)
            raise

    async def _fetch_data(self, url: str) -> str:
        """异步获取数据。

        Args:
            url: 请求 URL

        Returns:
            响应文本

        Raises:
            NetworkErrorException: 当网络连接失败或超时时
            ProviderServiceErrorException: 当 HTTP 状态码不是 200 时
        """
        if self.session is None:
            raise RuntimeError("会话未初始化，请使用 async with 语句或手动设置 session")

        try:
            async with self.session.get(url) as response:
                # 检查 HTTP 状态码
                if response.status != 200:
                    raise ProviderServiceErrorException(
                        stock_code=url.split("=")[-1],
                        status_code=response.status,
                        reason=f"HTTP 状态码: {response.status}",
                    )

                # 读取响应文本
                text = await response.text()

                # 检查响应是否为空
                if not text or text.strip() == "":
                    raise NetworkErrorException(
                        stock_code=url.split("=")[-1],
                        reason="数据提供者返回空响应",
                    )

                return text

        except aiohttp.ClientError as e:
            raise NetworkErrorException(
                stock_code=url.split("=")[-1],
                reason=f"网络请求失败: {e}",
            ) from e

        except asyncio.TimeoutError as e:
            raise NetworkErrorException(
                stock_code=url.split("=")[-1],
                reason=f"请求超时（{self.config.timeout} 秒）",
            ) from e

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
            InvalidStockCodeException: 当股票代码格式不正确时抛出
        """
        if not stock_code or len(stock_code) != 8:
            raise InvalidStockCodeException(f'无效的股票代码格式: "{stock_code}"，应为8位字符（如 sh600000 或 sz000001）')

        prefix = stock_code[:2].lower()
        suffix = stock_code[2:]

        if prefix not in ("sh", "sz"):
            raise InvalidStockCodeException(f'无效的股票代码格式: "{stock_code}"，应以 "sh" 或 "sz" 开头')

        if not suffix.isdigit():
            raise InvalidStockCodeException(f'无效的股票代码格式: "{stock_code}"，后6位应为数字')

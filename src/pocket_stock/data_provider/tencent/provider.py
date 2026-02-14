"""腾讯财经数据提供者。"""

import aiohttp

from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    NetworkError,
    ProviderServiceError,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.provider import BaseStockDataProvider
from pocket_stock.data_provider.tencent.parser import TencentFinanceParser


class TencentStockDataProvider(BaseStockDataProvider):
    """腾讯财经数据提供者。

    该类提供从腾讯财经获取股票实时行情的异步接口。

    Attributes:
        config: 配置对象
        session: aiohttp 异步 HTTP 客户端会话
        parser: 数据解析器

    Examples:
        >>> config = ProviderConfig(timeout=10.0)
        >>> provider = TencentStockDataProvider(config)
        >>> async with provider:
        ...     quote = await provider.get("sh600000")
        ...     print(f"股票名称: {quote.name}, 当前价格: {quote.current_price}")
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
            >>> provider = TencentStockDataProvider(config)
        """
        super().__init__(config, session)
        self.parser = TencentFinanceParser()

    async def _get(self, stock_code: str) -> StockQuote:
        """获取股票行情数据。

        向腾讯财经 API 发起异步 HTTP GET 请求，并解析返回的数据。

        Args:
            stock_code: 股票代码

        Returns:
            股票行情数据对象

        Raises:
            NetworkError: 当网络连接失败或超时时
            ProviderServiceError: 当 HTTP 状态码不是 200 时
        """
        if self.session is None:
            raise RuntimeError("会话未初始化，请使用 async with 语句或手动设置 session")

        # 构建 API URL
        url = self._API_URL.format(stock_code=stock_code)

        try:
            async with self.session.get(url) as response:
                # 检查 HTTP 状态码
                if response.status != 200:
                    raise ProviderServiceError(
                        stock_code=stock_code,
                        status_code=response.status,
                        reason=f"HTTP 状态码: {response.status}",
                    )

                # 读取响应文本
                text = await response.text()

                # 检查响应是否为空
                if not text or text.strip() == "":
                    raise NetworkError(
                        stock_code=stock_code,
                        reason="数据提供者返回空响应",
                    )

                # 解析数据并返回
                return await self.parser.parse(text, stock_code)

        except aiohttp.ClientError as e:
            raise NetworkError(
                stock_code=stock_code,
                reason=f"网络请求失败: {e}",
            ) from e

        except TimeoutError as e:
            raise NetworkError(
                stock_code=stock_code,
                reason=f"请求超时（{self.config.timeout} 秒）",
            ) from e

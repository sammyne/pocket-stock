"""股票行情查询命令行工具。

这是一个极简的命令行工具，用于查询指定股票的实时行情信息。
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from pocket_stock.cli.formatter import format_stock_quote
from pocket_stock.data_provider.config import ProviderConfig
from pocket_stock.data_provider.exceptions import (
    DataParseException,
    DataValidationException,
    InvalidStockCodeException,
    NetworkErrorException,
    ProviderServiceErrorException,
)
from pocket_stock.data_provider.models import StockQuote
from pocket_stock.data_provider.provider import StockDataProvider


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数。

    Returns:
        解析后的参数对象

    Examples:
        >>> args = parse_arguments()
        >>> args.stock_code
        'sh600000'
    """
    parser = argparse.ArgumentParser(
        description="股票行情查询工具 - 查询指定股票的实时行情信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s sh600000     # 查询浦发银行
  %(prog)s sz000001     # 查询平安银行
  %(prog)s -t 5 sh600000 # 设置超时时间为 5 秒

注意事项:
  - 股票代码格式: 市场代码(2位) + 股票编号(6位)
  - 市场代码: sh(上海) 或 sz(深圳)
  - 示例: sh600000, sz000001
        """,
    )

    parser.add_argument(
        "stock_code",
        help="股票代码（如 sh600000, sz000001）",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=10.0,
        help="请求超时时间（秒），默认 10 秒",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser.parse_args()


async def fetch_stock_quote(stock_code: str, timeout: float) -> StockQuote:
    """异步获取股票行情数据。

    Args:
        stock_code: 股票代码
        timeout: 超时时间（秒）

    Returns:
        股票行情数据对象

    Raises:
        InvalidStockCodeException: 股票代码无效
        NetworkErrorException: 网络错误
        ProviderServiceErrorException: 服务错误
    """
    config = ProviderConfig(timeout=timeout)
    async with StockDataProvider(config) as provider:
        quote = await provider.get_stock_quote(stock_code)
    return quote


def handle_exception(e: Exception, stock_code: str | None = None) -> int:
    """处理异常并返回退出码。

    Args:
        e: 异常对象
        stock_code: 股票代码（可选）

    Returns:
        退出码：0 表示成功，非 0 表示失败
    """
    code = stock_code if stock_code else "未知"

    if isinstance(e, InvalidStockCodeException):
        print(f"错误: 股票代码格式无效", file=sys.stderr)
        print(f"  股票代码: {code}", file=sys.stderr)
        print(f"  提示: 格式应为 sh 或 sz 开头，后跟 6 位数字，如 sh600000", file=sys.stderr)
        return 1

    if isinstance(e, NetworkErrorException):
        print(f"错误: 网络连接失败", file=sys.stderr)
        print(f"  股票代码: {code}", file=sys.stderr)
        print(f"  原因: {e.reason}", file=sys.stderr)
        return 2

    if isinstance(e, ProviderServiceErrorException):
        print(f"错误: 数据服务异常", file=sys.stderr)
        print(f"  股票代码: {code}", file=sys.stderr)
        print(f"  状态码: {e.status_code}", file=sys.stderr)
        print(f"  原因: {e.reason}", file=sys.stderr)
        return 3

    if isinstance(e, (DataParseException, DataValidationException)):
        print(f"错误: 数据解析失败", file=sys.stderr)
        print(f"  股票代码: {code}", file=sys.stderr)
        print(f"  详情: {e.message if isinstance(e, DataValidationException) else e.detail}", file=sys.stderr)
        return 4

    # 处理未预期的异常
    print(f"错误: 发生未知错误", file=sys.stderr)
    print(f"  股票代码: {code}", file=sys.stderr)
    print(f"  异常类型: {type(e).__name__}", file=sys.stderr)
    print(f"  异常信息: {e}", file=sys.stderr)
    return 5


async def async_main() -> int:
    """异步主函数。

    Returns:
        退出码：0 表示成功，非 0 表示失败
    """
    # 解析命令行参数
    args = parse_arguments()
    stock_code = args.stock_code
    timeout = args.timeout

    # 参数验证
    if timeout <= 0:
        print("错误: 超时时间必须大于 0", file=sys.stderr)
        return 1

    # 获取股票行情
    try:
        quote = await fetch_stock_quote(stock_code, timeout)
        # 格式化输出
        print(format_stock_quote(quote))
        return 0

    except (InvalidStockCodeException, NetworkErrorException, ProviderServiceErrorException, DataParseException, DataValidationException) as e:
        return handle_exception(e, stock_code)

    except Exception as e:
        return handle_exception(e, stock_code)


def main() -> None:
    """命令行工具主入口。

    该函数是程序的入口点，负责启动异步事件循环并执行主逻辑。

    Examples:
        >>> # 在命令行中执行
        >>> python -m pocket_stock.cli sh600000
    """
    try:
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n操作已取消", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()
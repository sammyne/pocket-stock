"""格式化输出模块。

提供将股票行情数据格式化为美观的表格输出的功能。
"""

from __future__ import annotations

from pocket_stock.data_provider.models import StockQuote


def format_stock_quote(quote: StockQuote) -> str:
    """格式化股票行情数据为表格形式。

    Args:
        quote: 股票行情数据对象

    Returns:
        格式化后的表格字符串

    Examples:
        >>> quote = StockQuote(
        ...     stock_code="sh600000",
        ...     name="浦发银行",
        ...     current_price=10.25,
        ...     change=0.15,
        ...     change_percent=1.48
        ... )
        >>> print(format_stock_quote(quote))
        股票行情信息
        ==============
        股票代码: sh600000
        股票名称: 浦发银行
        ...
    """
    # 构建表格内容
    lines: list[str] = []
    lines.append("股票行情信息")
    lines.append("=" * 48)
    lines.append(f"股票代码: {quote.stock_code}")
    lines.append(f"股票名称: {quote.name}")
    lines.append(f"当前价格: {quote.current_price:.2f} 元")

    # 格式化涨跌额和涨跌幅
    change_str = _format_change(quote.change, quote.current_price)
    lines.append(f"涨跌额:   {change_str}")

    change_percent_str = _format_change_percent(quote.change_percent)
    lines.append(f"涨跌幅:   {change_percent_str}")

    # 格式化价格信息
    lines.append(f"开盘价:   {quote.open_price:.2f} 元" if quote.open_price else "开盘价:   --")
    lines.append(f"收盘价:   {quote.close_price:.2f} 元" if quote.close_price else "收盘价:   --")
    lines.append(f"最高价:   {quote.high_price:.2f} 元" if quote.high_price else "最高价:   --")
    lines.append(f"最低价:   {quote.low_price:.2f} 元" if quote.low_price else "最低价:   --")

    # 格式化成交信息
    lines.append(f"成交量:   {_format_volume(quote.volume)}")
    lines.append(f"成交额:   {_format_turnover(quote.turnover)}")

    # 时间戳
    if quote.timestamp:
        lines.append(f"更新时间: {quote.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    lines.append("=" * 48)

    return "\n".join(lines)


def _format_change(change: float | None, current_price: float) -> str:
    """格式化涨跌额。

    Args:
        change: 涨跌额
        current_price: 当前价格

    Returns:
        格式化后的字符串，带颜色标识
    """
    if change is None or change == 0:
        return f"0.00 元"
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.2f} 元"


def _format_change_percent(change_percent: float | None) -> str:
    """格式化涨跌幅。

    Args:
        change_percent: 涨跌幅

    Returns:
        格式化后的字符串，带颜色标识
    """
    if change_percent is None or change_percent == 0:
        return "0.00%"
    sign = "+" if change_percent > 0 else ""
    return f"{sign}{change_percent:.2f}%"


def _format_volume(volume: int | None) -> str:
    """格式化成交量。

    Args:
        volume: 成交量（股）

    Returns:
        格式化后的字符串，自动转换单位
    """
    if volume is None or volume == 0:
        return "0"

    if volume >= 100000000:
        return f"{volume / 100000000:.2f} 亿股"
    elif volume >= 10000:
        return f"{volume / 10000:.2f} 万股"
    else:
        return f"{volume} 股"


def _format_turnover(turnover: float | None) -> str:
    """格式化成交额。

    Args:
        turnover: 成交额（元）

    Returns:
        格式化后的字符串，自动转换单位
    """
    if turnover is None or turnover == 0:
        return "0 元"

    if turnover >= 100000000:
        return f"{turnover / 100000000:.2f} 亿元"
    elif turnover >= 10000:
        return f"{turnover / 10000:.2f} 万元"
    else:
        return f"{turnover:.2f} 元"

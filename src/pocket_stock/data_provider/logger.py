"""日志记录模块。"""

import logging
import traceback
from datetime import datetime
from typing import Any

# 模块级日志器
_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """获取或创建模块级日志器。

    Returns:
        日志器实例
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger("pocket_stock.data_provider")

    # 确保日志器至少有一个处理器
    if not _logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

    return _logger


async def log_request(stock_code: str, **kwargs: Any) -> None:
    """异步记录数据请求信息。

    Args:
        stock_code: 股票代码
        **kwargs: 其他请求参数

    Examples:
        >>> await log_request("sh600000", timeout=10.0)
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"[请求] 股票代码: {stock_code}, 时间: {timestamp}, 参数: {params}")


async def log_response(stock_code: str, elapsed_time: float, **kwargs: Any) -> None:
    """异步记录数据响应信息。

    Args:
        stock_code: 股票代码
        elapsed_time: 响应耗时（秒）
        **kwargs: 其他响应信息

    Examples:
        >>> await log_response("sh600000", 0.5, status=200, data_size=1024)
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"[响应] 股票代码: {stock_code}, 时间: {timestamp}, 耗时: {elapsed_time:.3f}秒, 信息: {params}")


async def log_error(
    error: Exception,
    stock_code: str | None = None,
    **kwargs: Any,
) -> None:
    """异步记录错误信息。

    Args:
        error: 异常对象
        stock_code: 股票代码（可选）
        **kwargs: 其他上下文信息

    Examples:
        >>> try:
        ...     raise ValueError("测试错误")
        >>> except ValueError as e:
        ...     await log_error(e, stock_code="sh600000")
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    error_type = type(error).__name__
    error_msg = str(error)

    # 构建上下文信息
    context_parts = []
    if stock_code:
        context_parts.append(f"股票代码: {stock_code}")
    if kwargs:
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        context_parts.append(f"上下文: {params}")

    context = ", ".join(context_parts) if context_parts else "无"

    logger.error(f"[错误] 类型: {error_type}, 消息: {error_msg}, 时间: {timestamp}, {context}")

    # 记录堆栈跟踪（仅在 DEBUG 级别）
    if logger.isEnabledFor(logging.DEBUG):
        stack_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logger.debug(f"[堆栈] {stack_trace}")


def setup_logger() -> None:
    """设置日志器。"""
    logger = get_logger()
    logger.setLevel(logging.INFO)

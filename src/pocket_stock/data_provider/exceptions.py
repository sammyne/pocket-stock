"""自定义异常类。"""


class DataProviderError(Exception):
    """数据提供者基础异常类。

    所有数据提供者相关的自定义异常都应继承此类。

    Attributes:
        message: 异常消息
    """

    def __init__(self, message: str) -> None:
        """初始化异常。

        Args:
            message: 异常消息
        """
        self.message = message
        super().__init__(self.message)


class InvalidStockCodeException(DataProviderError):
    """股票代码无效异常。

    当传入的股票代码为空、格式不正确或不存在时抛出此异常。

    Examples:
        >>> raise InvalidStockCodeException("股票代码不能为空")
    """


class NetworkErrorException(DataProviderError):
    """网络错误异常。

    当网络连接失败、超时或发生其他网络相关错误时抛出此异常。

    Attributes:
        stock_code: 股票代码
        reason: 错误原因

    Examples:
        >>> raise NetworkErrorException("sh600000", "连接超时")
    """

    def __init__(self, stock_code: str, reason: str) -> None:
        """初始化异常。

        Args:
            stock_code: 股票代码
            reason: 错误原因
        """
        self.stock_code = stock_code
        self.reason = reason
        super().__init__(f"获取股票 {stock_code} 数据时发生网络错误: {reason}")


class ProviderServiceErrorException(DataProviderError):
    """数据提供者服务错误异常。

    当腾讯财经等数据提供者返回 HTTP 错误状态码时抛出此异常。

    Attributes:
        stock_code: 股票代码
        status_code: HTTP 状态码
        reason: 错误原因

    Examples:
        >>> raise ProviderServiceErrorException("sh600000", 404, "资源未找到")
    """

    def __init__(self, stock_code: str, status_code: int, reason: str) -> None:
        """初始化异常。

        Args:
            stock_code: 股票代码
            status_code: HTTP 状态码
            reason: 错误原因
        """
        self.stock_code = stock_code
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"数据提供者返回错误（股票: {stock_code}, 状态码: {status_code}, 原因: {reason}）")


class DataParseException(DataProviderError):
    """数据解析错误异常。

    当返回的数据格式不符合预期或解析失败时抛出此异常。

    Attributes:
        stock_code: 股票代码
        detail: 解析错误的详细信息

    Examples:
        >>> raise DataParseException("sh600000", "JSON 格式错误")
    """

    def __init__(self, stock_code: str, detail: str) -> None:
        """初始化异常。

        Args:
            stock_code: 股票代码
            detail: 解析错误的详细信息
        """
        self.stock_code = stock_code
        self.detail = detail
        super().__init__(f"解析股票 {stock_code} 的数据时发生错误: {detail}")


class DataValidationException(DataProviderError):
    """数据验证错误异常。

    当数据验证失败时抛出此异常。

    Attributes:
        message: 验证失败的详细信息

    Examples:
        >>> raise DataValidationException("当前价格不能为负数")
    """

    def __init__(self, message: str) -> None:
        """初始化异常。

        Args:
            message: 验证失败的详细信息
        """
        # 先设置 message 属性为原始消息
        self.message = message
        # 直接调用 Exception 的构造函数，避免被 DataProviderError 覆盖 message
        Exception.__init__(self, f"数据验证失败: {message}")

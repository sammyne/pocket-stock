"""
搜索模块异常类

定义搜索模块相关的异常类型。
"""


class SearchError(Exception):
    """搜索模块基础异常类

    所有搜索模块异常的基类。
    """

    def __init__(self, message: str, *args: object) -> None:
        """初始化异常

        Args:
            message: 错误消息
            *args: 额外的参数
        """
        self.message = message
        super().__init__(message, *args)


class ConfigurationError(SearchError):
    """配置异常

    当配置无效或缺失时抛出。
    """

    def __init__(self, message: str = "配置错误", *args: object) -> None:
        super().__init__(message, *args)


class MissingAPIKeyError(ConfigurationError):
    """API Key 缺失异常

    当 Tavily API key 未配置时抛出。
    """

    def __init__(self, message: str = "TAVILY_API_KEY 环境变量未设置", *args: object) -> None:
        super().__init__(message, *args)


class NetworkError(SearchError):
    """网络异常

    当网络请求失败时抛出。
    """

    def __init__(self, message: str = "网络请求失败", *args: object) -> None:
        super().__init__(message, *args)


class ServiceError(SearchError):
    """服务异常

    当搜索服务返回错误时抛出。
    """

    def __init__(self, message: str = "搜索服务错误", *args: object, status_code: int | None = None) -> None:
        """初始化服务异常

        Args:
            message: 错误消息
            *args: 额外的参数
            status_code: HTTP 状态码
        """
        self.status_code = status_code
        super().__init__(message, *args)


class ValidationError(SearchError):
    """验证异常

    当输入参数验证失败时抛出。
    """

    def __init__(self, message: str = "参数验证失败", *args: object) -> None:
        super().__init__(message, *args)


class RateLimitError(ServiceError):
    """速率限制异常

    当达到 API 速率限制时抛出。
    """

    def __init__(
        self, message: str = "达到 API 速率限制", *args: object, limit: int | None = None
    ) -> None:
        """初始化速率限制异常

        Args:
            message: 错误消息
            *args: 额外的参数
            limit: 速率限制数值
        """
        self.limit = limit
        super().__init__(message, *args)


class AuthenticationError(ServiceError):
    """认证异常

    当 API 认证失败时抛出。
    """

    def __init__(self, message: str = "API 认证失败，请检查 API Key", *args: object) -> None:
        super().__init__(message, *args, status_code=401)

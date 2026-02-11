"""自定义异常类模块。

定义了 LLM 股票分析模块的所有自定义异常。
"""


class LLMAnalysisError(Exception):
    """LLM 分析相关异常的基类。

    所有 LLM 分析模块的自定义异常都继承自此类。
    """


class ConfigurationError(LLMAnalysisError):
    """配置错误异常。

    当缺少必需的配置项或配置无效时抛出。
    """

    pass


class LLMApiTimeoutError(LLMAnalysisError):
    """LLM API 调用超时异常。

    当 LLM API 调用超过预设时间限制时抛出。
    """

    pass


class LLMAuthenticationError(LLMAnalysisError):
    """LLM API 认证错误异常。

    当 API 密钥无效或认证失败时抛出。
    """

    pass


class LLMServiceError(LLMAnalysisError):
    """LLM 服务错误异常。

    当 LLM 服务返回错误（如 500 错误）时抛出。
    """

    pass


class NetworkConnectionError(LLMAnalysisError):
    """网络连接错误异常。

    当无法连接到 LLM 服务时抛出。
    """

    pass


class LLMResponseParseError(LLMAnalysisError):
    """LLM 响应解析错误异常。

    当无法解析 LLM 返回的响应或响应格式不符合预期时抛出。
    """

    pass
